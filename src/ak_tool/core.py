import os
import subprocess
import time
import json
import logging
import yaml
from ak_tool.config import AKConfig


class AWSManager:
    """
    Manages AWS MFA login, storing credentials in the specified credentials file.

    This class handles AWS MFA-based authentication and stores the resulting credentials
    in an AWS CLI-compatible credentials file. It also provides an `export` command
    for updating environment variables.

    Attributes:
        config (AKConfig): Configuration settings for AWS login.
        logger (logging.Logger): Logger instance for debugging and error reporting.
        aws_profile_name (str): The name of the AWS profile being used.
    """

    def __init__(self, config: AKConfig, logger: logging.Logger, aws_profile_name: str):
        """
        Initializes the AWSManager with configuration and logging.

        Args:
            config (AKConfig): Configuration settings.
            logger (logging.Logger): Logger instance.
            aws_profile_name (str): Name of the AWS profile to use.
        """
        self.config = config
        self.logger = logger
        self.aws_profile_name = aws_profile_name

    def mfa_login(self, mfa_code: str) -> str:
        """
        Perform AWS MFA login using the original profile and MFA code.

        This method retrieves a temporary AWS session token using MFA,
        stores it in the AWS credentials file, and returns a shell export
        command to set `AWS_PROFILE`.

        Args:
            mfa_code (str): The MFA code for authentication.

        Returns:
            str: The `export AWS_PROFILE=authenticated_profile` command.

        Raises:
            RuntimeError: If the AWS login attempt fails.

        Example:
            ```python
            aws = AWSManager(config, logger, "nuvo")
            export_line = aws.mfa_login("123456")
            print(export_line)
            ```

            ```shell
            export AWS_PROFILE=nuvo-root-mfa
            ```
        """
        self.logger.debug(f"AWSManager: MFA login for {self.aws_profile_name}")
        aws_profile = self.config.get_aws_profile(self.aws_profile_name)

        cmd = [
            "aws",
            "--profile",
            aws_profile["original_profile"],
            "sts",
            "get-session-token",
            "--serial-number",
            aws_profile["mfa_serial"],
            "--token-code",
            mfa_code,
            "--duration-seconds",
            str(aws_profile["token_validity_seconds"]),
        ]

        self.logger.debug(f"AWSManager: Running command: {cmd}")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"AWS login failed:\n{proc.stderr}")

        data = json.loads(proc.stdout)
        self._update_credentials_file(aws_profile["authenticated_profile"], data)

        # switch to default kube config
        kube = KubeManager(self.config, self.logger)
        commands = kube.switch_config(self.config.default_kube_config)
        return commands

    def _update_credentials_file(self, profile: str, data: dict) -> None:
        """
        Updates the AWS credentials file with the new session token.

        Args:
            profile (str): The AWS profile to store the credentials under.
            data (dict): The session token data.

        """
        credentials_file = self.config.credentials_file
        import configparser

        parser = configparser.ConfigParser()
        parser.read(credentials_file)
        if not parser.has_section(profile):
            parser.add_section(profile)

        parser[profile]["aws_access_key_id"] = data["Credentials"]["AccessKeyId"]
        parser[profile]["aws_secret_access_key"] = data["Credentials"][
            "SecretAccessKey"
        ]
        parser[profile]["aws_session_token"] = data["Credentials"]["SessionToken"]

        with open(credentials_file, "w") as f:
            parser.write(f)


class KubeManager:
    """
    Manages Kubernetes kubeconfig switching and token handling.

    This class provides functionality to switch Kubernetes configurations,
    refresh AWS-based authentication tokens, and ensure valid kubeconfig
    contexts.

    Attributes:
        config (AKConfig): Configuration settings.
        logger (logging.Logger): Logger instance.
    """

    def __init__(self, config: AKConfig, logger: logging.Logger):
        """
        Initializes the KubeManager with configuration and logging.

        Args:
            config (AKConfig): Configuration settings.
            logger (logging.Logger): Logger instance.
        """
        self.config = config
        self.logger = logger

    def switch_config(self, kubeconfig_name: str) -> str:
        """
        Switch to a specified kubeconfig, resolving AWS-based authentication tokens.

        This method ensures that the kubeconfig is copied to a temporary location
        and all `aws-iam-authenticator` references are replaced with static tokens.

        Args:
            kubeconfig_name (str): Name of the kubeconfig to switch to.

        Returns:
            str: The `export KUBECONFIG=...` command.

        Raises:
            FileNotFoundError: If the kubeconfig does not exist.
        """
        self.logger.debug(f"Switching config to {kubeconfig_name}")
        temp_file, timestamp_file = self._get_temp_file_paths(kubeconfig_name)

        if self._needs_refresh(temp_file, timestamp_file):
            self._refresh_tokens(kubeconfig_name, temp_file, timestamp_file)

        # get the current context from the kubeconfig
        current_context = self._get_current_context(temp_file)

        # switch to the new kubeconfig and append f"export KUBECONFIG={temp_file}" to
        return f"export KUBECONFIG={temp_file}\n" + self.switch_context(current_context)

    def _get_current_context(self, kubeconfig_path: str) -> str:
        """
        Gets the current Kubernetes context from the specified kubeconfig.

        Args:
            kubeconfig_path (str): Path to the kubeconfig file.

        Returns:
            str: The name of the current context.
        """
        with open(kubeconfig_path, "r") as f:
            kubeconfig = yaml.safe_load(f)

        return kubeconfig.get("current-context", "")

    def _get_temp_file_paths(self, kubeconfig_name: str) -> tuple:
        """
        Gets the paths for the temporary kubeconfig and its timestamp file.

        Args:
            kubeconfig_name (str): The name of the kubeconfig.

        Returns:
            tuple: Paths for (temporary kubeconfig, timestamp file).
        """
        temp_file = os.path.join(self.config.kube_temp_dir, f"{kubeconfig_name}-temp")
        timestamp_file = os.path.join(
            self.config.kube_temp_dir, f"{kubeconfig_name}-temp.timestamp"
        )
        return temp_file, timestamp_file

    def _needs_refresh(self, temp_file: str, timestamp_file: str) -> bool:
        """
        Determines if a token refresh is required based on token validity.

        Args:
            temp_file (str): Path to the temporary kubeconfig.
            timestamp_file (str): Path to the timestamp file.

        Returns:
            bool: True if a refresh is required, False otherwise.
        """
        if not os.path.exists(temp_file) or not os.path.exists(timestamp_file):
            return True

        try:
            with open(timestamp_file) as f:
                token_age = int(time.time()) - int(f.read().strip())
            return token_age >= self.config.kube_token_validity_seconds
        except ValueError:
            return True

    def _refresh_tokens(
        self, kubeconfig_name: str, temp_file: str, timestamp_file: str
    ) -> None:
        """
        Refreshes authentication tokens by copying the original kubeconfig,
        replacing authentication commands, and updating the timestamp.

        Args:
            kubeconfig_name (str): The kubeconfig name.
            temp_file (str): The temporary kubeconfig file path.
            timestamp_file (str): The timestamp file path.
        """
        self.logger.debug(f"Refreshing tokens for {kubeconfig_name}")
        original_file = os.path.join(self.config.kube_configs_dir, kubeconfig_name)
        os.makedirs(self.config.kube_temp_dir, exist_ok=True)
        subprocess.run(["cp", original_file, temp_file])

        self._replace_exec_with_static_tokens(temp_file)
        self._update_timestamp(timestamp_file)

    def _replace_exec_with_static_tokens(self, kubeconfig_path: str) -> None:
        """
        Replaces `aws-iam-authenticator` exec commands in kubeconfig with static tokens.

        This method iterates through the users in the kubeconfig, identifies those
        that use `aws-iam-authenticator` for authentication, and replaces their
        exec-based authentication with a static token obtained from AWS.

        Args:
            kubeconfig_path (str): Path to the kubeconfig file that needs modification.

        Raises:
            RuntimeError: If token generation fails.
        """
        self.logger.debug(
            f"Replacing exec commands with static tokens in {kubeconfig_path}"
        )

        with open(kubeconfig_path, "r") as f:
            kubeconfig = yaml.safe_load(f)

        modified = False

        for user in kubeconfig.get("users", []):
            exec_info = user.get("user", {}).get("exec", {})
            # if exec_info.get("command") contains the word "aws-iam-authenticator"
            if "aws-iam-authenticator" in exec_info.get("command", ""):
                aws_profile = self._extract_aws_profile(exec_info)
                if aws_profile:
                    self.logger.debug(
                        f"Generating static token for user {user['name']} "
                        f"with profile {aws_profile}"
                    )
                    user["user"]["token"] = self._generate_static_token(
                        aws_profile, exec_info.get("args", [])
                    )
                    user["user"].pop("exec", None)
                    modified = True

        if modified:
            with open(kubeconfig_path, "w") as f:
                yaml.safe_dump(kubeconfig, f)
            self.logger.info(
                f"Kubeconfig {kubeconfig_path} updated with static tokens."
            )

    def _extract_aws_profile(self, exec_info: dict) -> str:
        """
        Extracts the `AWS_PROFILE` value from the exec command's environment variables.

        Args:
            exec_info (dict): The exec block from the kubeconfig user definition.

        Returns:
            str: The AWS profile name, or None if not found.
        """
        return next(
            (
                env["value"]
                for env in exec_info.get("env", [])
                if env["name"] == "AWS_PROFILE"
            ),
            None,
        )

    def _generate_static_token(self, aws_profile: str, args: list) -> str:
        """
        Generates a static Kubernetes API token using `aws-iam-authenticator`.

        Args:
            aws_profile (str): The AWS profile to use.
            args (list): Additional arguments required for token generation.

        Returns:
            str: A valid Kubernetes authentication token.

        Raises:
            RuntimeError: If the token generation process fails.
        """
        env = os.environ.copy()
        env["AWS_PROFILE"] = aws_profile

        result = subprocess.run(
            ["aws-iam-authenticator", "token"] + args,
            capture_output=True,
            text=True,
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to generate token with aws-iam-authenticator: {result.stderr}"
            )

        return yaml.safe_load(result.stdout)["status"]["token"]

    def _update_timestamp(self, timestamp_file: str) -> None:
        """
        Updates the timestamp file with the current time.

        Args:
            timestamp_file (str): Path to the timestamp file.
        """
        with open(timestamp_file, "w") as f:
            f.write(str(int(time.time())))

    def switch_context(self, context_name: str) -> str:
        """
        Switches the active Kubernetes context and updates the shell prompt
        with context info.

        The prompt includes Git branch, original kubeconfig name, and current context,
        formatted for Bash, Zsh, or Fish shells.
        """
        kubeconfig = os.environ.get("KUBECONFIG", "")
        if not kubeconfig or not os.path.exists(kubeconfig):
            raise EnvironmentError("No valid KUBECONFIG set.")

        self._ensure_valid_token(kubeconfig, context_name)
        self._run_kubectl_command(
            ["config", "use-context", context_name, "--kubeconfig", kubeconfig]
        )

        shell_type = self._detect_shell_type()  # Assume this method detects the shell
        kubeconfig_name = os.path.basename(kubeconfig)
        # remove the -temp suffix if it exists
        kubeconfig_name = kubeconfig_name.replace("-temp", "")

        git_cmd = (
            "branch=$(git branch --show-current 2>/dev/null); "
            'if [ -n "$branch" ]; then echo "($branch)"; fi'
        )

        if shell_type == "bash":
            return self._bash_prompt(kubeconfig_name, context_name, git_cmd)
        elif shell_type == "zsh":
            return self._zsh_prompt(kubeconfig_name, context_name, git_cmd)
        elif shell_type == "fish":
            return self._fish_prompt(kubeconfig_name, context_name)
        else:
            raise RuntimeError(f"Unsupported shell: {shell_type}")

    def _bash_prompt(
        self, kubeconfig_name: str, context_name: str, git_cmd: str
    ) -> str:
        git_part = rf"\[\e[31m\]$({git_cmd})\[\e[0m\]"
        kube_part = rf"\[\e[36m\]<{kubeconfig_name}>\e[0m"
        context_part = rf"\[\e[34m\]{{{context_name}}}\[\e[0m\]"
        parts = f"{git_part} {kube_part} {context_part}"
        return (
            'if [ -z "$ORIG_PS1" ]; then ORIG_PS1="${PS1%\\\\\\$*}"; fi\n'
            f'export PS1="$ORIG_PS1 {parts} \\\\$ "'
        )

    def _zsh_prompt(self, kubeconfig_name: str, context_name: str, git_cmd: str) -> str:
        git_part = rf"%F{{red}}$({git_cmd})%f"
        kube_part = rf"%F{{cyan}}<{kubeconfig_name}>%f"
        context_part = rf"%F{{blue}}{{{context_name}}}%f"
        parts = f"{git_part} {kube_part} {context_part}"
        return (
            'if [ -z "$ORIG_PROMPT" ]; then ORIG_PROMPT="${PROMPT%%#*}"; fi\n'
            f'export PROMPT="$ORIG_PROMPT {parts} %# "'
        )

    def _fish_prompt(self, kubeconfig_name: str, context_name: str) -> str:
        return f"""
        set -gx KUBE_PROMPT_KUBECONFIG "{kubeconfig_name}"
        set -gx KUBE_PROMPT_CONTEXT "{context_name}"
        if not functions -q _kube_original_fish_prompt
            functions -c fish_prompt _kube_original_fish_prompt
            function fish_prompt
                _kube_original_fish_prompt
                set -l git_branch (git branch --show-current 2>/dev/null)
                if test -n "$git_branch"
                    printf ' (set_color red)(%%s)(set_color normal)' "$git_branch"
                end
                printf ' (set_color cyan)<%%s>(set_color normal)' \
                    "$KUBE_PROMPT_KUBECONFIG"
                printf ' (set_color blue){{%%s}}(set_color normal)' \
                    "$KUBE_PROMPT_CONTEXT"
            end
        end
        """

    def _detect_shell_type(self) -> str:
        """
        Detects the current shell type by checking the parent process and environment
        variables.

        Returns:
            str: Shell type (bash/zsh/fish). Defaults to bash if detection fails.
        """
        # Try to detect using parent process
        try:
            ppid = os.getppid()
            result = subprocess.run(
                ["ps", "-p", str(ppid), "-o", "comm="],
                capture_output=True,
                text=True,
                check=True,
            )
            shell_name = result.stdout.strip().lower()

            # Handle login shells that start with '-'
            if shell_name.startswith("-"):
                shell_name = shell_name[1:]

            if shell_name in {"bash", "zsh", "fish"}:
                return shell_name
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # Fallback if ps isn't available or command fails

        # Fallback to SHELL environment variable
        shell_path = os.environ.get("SHELL", "")
        shell_name = os.path.basename(shell_path).lower()

        if "bash" in shell_name:
            return "bash"
        if "zsh" in shell_name:
            return "zsh"
        if "fish" in shell_name:
            return "fish"

        # Default to bash if all detection methods fail
        return "bash"

    def _ensure_valid_token(self, kubeconfig: str, context_name: str) -> None:
        """
        Ensures that the specified Kubernetes context has a valid authentication token.

        Args:
            kubeconfig (str): The kubeconfig file path.
            context_name (str): The name of the context.
        """

        # resolve original kubeconfig from kubeconfig-temp file by removing -temp
        original_kubeconfig = kubeconfig.replace("-temp", "")
        # original_kubeconfig is in the folder ~/.kubeconfigs/<kubeconfig_name>
        # while the temp file is in ~/.kubeconfigs_temp/<kubeconfig_name>-temp
        # need to update the path as well
        original_kubeconfig = os.path.join(
            self.config.kube_configs_dir, os.path.basename(original_kubeconfig)
        )

        temp_file, timestamp_file = self._get_temp_file_paths(original_kubeconfig)

        if not os.path.exists(original_kubeconfig):
            raise FileNotFoundError(f"Kubeconfig {original_kubeconfig} not found.")

        if self._needs_refresh(temp_file, timestamp_file):
            self._refresh_tokens(original_kubeconfig, temp_file, timestamp_file)

    def _run_kubectl_command(self, args: list) -> None:
        """
        Runs a kubectl command with the specified arguments.

        Args:
            args (list): The command arguments.
        """
        cmd = ["kubectl"] + args
        self.logger.debug(f"Running kubectl command: {cmd}")
        subprocess.run(cmd, check=True)
