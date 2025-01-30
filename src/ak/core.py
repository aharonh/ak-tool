import os
import subprocess
import time
import json
import logging

from .config import AKConfig


class AWSManager:
    """
    Manages AWS MFA login, storing credentials in the
    specified credentials file.
    """

    def __init__(self, config: AKConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    # sphenix docstring
    # Perform AWS MFA login using the original profile and mfa code,
    # store in the authenticated profile. Return the environment export
    # line for AWS_PROFILE.
    # 
    # Args:
    #     mfa_code (str): The MFA code to use for login.
    #
    # Returns:
    #     str: The environment export line for AWS_PROFILE.
    #
    # Raises:
    #     RuntimeError: If the login fails.
    # 
    # Example:
    #     ```python
    #     aws = AWSManager(config, logger)
    #     export_line = aws.mfa_login("123456")
    #     print(export_line)
    #     ```
    #
    #     ```shell
    #     export AWS_PROFILE=authenticated
    #     ```
    # 
    # Note:
    #     This method will update the credentials file with the new session token.
    #     The credentials file is expected to be in the format of the AWS CLI
    #     credentials file, with sections for each profile.
    #     The original profile is the profile to use for the initial login.
    #     The authenticated profile is the profile to store the authenticated
    #     credentials in.
    #     The MFA serial is the ARN of the MFA device to use for login.
    #     The token validity is the number of seconds the token is valid for.
    def mfa_login(self, mfa_code: str) -> str:
        """
        Perform AWS MFA login using the original profile and mfa code,
        store in the authenticated profile. Return the environment export
        line for AWS_PROFILE.
        """
        cmd = [
            "aws",
            "--profile",
            self.config.original_profile,
            "sts",
            "get-session-token",
            "--serial-number",
            self.config.mfa_serial,
            "--token-code",
            mfa_code,
            "--duration-seconds",
            
        ]
        self.logger.debug(f"AWSManager: Running command: {cmd}")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"AWS login failed:\n{proc.stderr}")

        data = json.loads(proc.stdout)
        credentials_file = self.config.credentials_file

        # Update credentials file to include the new session token
        import configparser

        parser = configparser.ConfigParser()
        parser.read(credentials_file)
        if not parser.has_section(self.config.authenticated_profile):
            parser.add_section(self.config.authenticated_profile)
        parser[self.config.authenticated_profile]["aws_access_key_id"] = data[
            "Credentials"
        ]["AccessKeyId"]
        parser[self.config.authenticated_profile]["aws_secret_access_key"] = data[
            "Credentials"
        ]["SecretAccessKey"]
        parser[self.config.authenticated_profile]["aws_session_token"] = data[
            "Credentials"
        ]["SessionToken"]
        with open(credentials_file, "w") as f:
            parser.write(f)

        # Return a shell export line, so the caller can `eval` it
        return f"export AWS_PROFILE={self.config.authenticated_profile}"


class KubeManager:
    """Manages the creation and usage of temporary kubeconfigs."""

    def __init__(self, config: AKConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def switch_config(self, kube_name: str) -> str:
        """
        Switch to a specified kubeconfig by copying
        ~/.kubeconfigs/<kube_name> to ~/.kubeconfigs_temp/<kube_name>-temp,
        if needed. Returns an `export KUBECONFIG=...` line.
        """
        original_file = os.path.join(self.config.kube_configs_dir, kube_name)
        if not os.path.exists(original_file):
            raise FileNotFoundError(
                f"Kubeconfig '{kube_name}' not found in "
                f"{self.config.kube_configs_dir}"
            )

        temp_file = os.path.join(self.config.kube_temp_dir, f"{kube_name}-temp")
        timestamp_file = os.path.join(
            self.config.kube_temp_dir, f"{kube_name}-temp.timestamp"
        )

        os.makedirs(self.config.kube_temp_dir, exist_ok=True)

        now = int(time.time())
        token_validity = self.config.token_validity_seconds

        need_refresh = True
        if os.path.exists(temp_file) and os.path.exists(timestamp_file):
            try:
                with open(timestamp_file) as f:
                    old_ts = int(f.read().strip())
                age = now - old_ts
                if age < token_validity:
                    need_refresh = False
            except ValueError:
                pass
        if need_refresh:
            self.logger.debug(
                f"KubeManager: copying original config for "
                f"{kube_name}, tokens are stale."
            )
            subprocess.run(["cp", original_file, temp_file])
            with open(timestamp_file, "w") as f:
                f.write(str(now))

        return f"export KUBECONFIG={temp_file}"

    def switch_context(self, context_name: str) -> str:
        """
        Switch context within the current KUBECONFIG. Potentially modifies
        prompt.
        """
        kubeconfig = os.environ.get("KUBECONFIG", "")
        if not kubeconfig or not os.path.exists(kubeconfig):
            raise EnvironmentError(
                "No valid KUBECONFIG set. " "Did you run `ak c <kube_name>` first?"
            )
        cmd = [
            "kubectl",
            "config",
            "use-context",
            context_name,
            "--kubeconfig",
            kubeconfig,
        ]
        self.logger.debug(f"KubeManager: switching context -> {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Could not switch context: {result.stderr}")

        # Return an instruction to update the prompt with the new context
        # We want it as follows:
        # user@computer current_folder {current_k8s_context} $
        return f'export PS1="\\u@\\h \\W [{context_name}] $ "'

    def force_refresh(self) -> None:
        """
        Force a token refresh by updating the timestamp file for the current
        KUBECONFIG so that next usage re-copies tokens.
        """
        kubeconfig = os.environ.get("KUBECONFIG", "")
        if not kubeconfig or not os.path.exists(kubeconfig):
            self.logger.warning("Cannot force-refresh: no valid KUBECONFIG.")
            return
        basename = os.path.basename(kubeconfig).replace("-temp", "")
        timestamp_file = os.path.join(
            self.config.kube_temp_dir, f"{basename}-temp.timestamp"
        )
        with open(timestamp_file, "w") as f:
            f.write(str(int(time.time()) - (2 * self.config.token_validity_seconds)))
        self.logger.info("Token refresh forced; next usage will regenerate if needed.")
