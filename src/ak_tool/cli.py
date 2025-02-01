import sys
import os
import subprocess
import click
from click.shell_completion import CompletionItem
from ak_tool.config import AKConfig
from ak_tool.logger import setup_logger
from ak_tool.core import AWSManager, KubeManager


def complete_aws_profile(ctx, param, incomplete):
    """
    Return a list of AWS profile names matching the incomplete text.

    Retrieves AWS profile names from the configuration sections that start with
    ``aws.`` and returns those that begin with the provided incomplete string.

    :param ctx: Click context.
    :param param: Click parameter.
    :param incomplete: Incomplete text typed by the user.
    :type incomplete: str
    :return: A list of CompletionItem objects with matching AWS profile names.
    :rtype: list[CompletionItem]
    """
    config = AKConfig()
    profiles = []
    for section in config._cp.sections():
        if section.startswith("aws."):
            profile_name = section[4:]  # e.g. "aws.home" -> "home"
            if profile_name.startswith(incomplete):
                profiles.append(CompletionItem(profile_name))
    return profiles


def complete_kube_name(ctx, param, incomplete):
    """
    Return a list of kubeconfig filenames matching the incomplete text.

    Scans the directory specified by the configuration for kubeconfigs and returns
    filenames that start with the provided incomplete string.

    :param ctx: Click context.
    :param param: Click parameter.
    :param incomplete: Incomplete text typed by the user.
    :type incomplete: str
    :return: A list of CompletionItem objects with matching kubeconfig filenames.
    :rtype: list[CompletionItem]
    """
    config = AKConfig()
    kube_dir = config.kube_configs_dir
    kube_dir = os.path.expanduser(kube_dir)

    if not os.path.isdir(kube_dir):
        return []

    items = []
    for fname in os.listdir(kube_dir):
        if fname.startswith(incomplete):
            items.append(CompletionItem(fname))
    return items


def complete_context_name(ctx, param, incomplete):
    """
    Return a list of Kubernetes context names matching the incomplete text.

    Executes the command ``kubectl config get-contexts -o name`` to retrieve context names,
    then filters and returns those that start with the provided incomplete string.

    :param ctx: Click context.
    :param param: Click parameter.
    :param incomplete: Incomplete text typed by the user.
    :type incomplete: str
    :return: A list of CompletionItem objects with matching Kubernetes context names.
    :rtype: list[CompletionItem]
    """
    try:
        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.split()
    except Exception:
        return []

    items = []
    for line in lines:
        if line.startswith(incomplete):
            items.append(CompletionItem(line))
    return items


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.option(
    "--aws-profile",
    help="Name of AWS sub-profile section, e.g. 'company', 'home'.",
    shell_complete=complete_aws_profile,
)
@click.pass_context
def ak(ctx, debug, aws_profile):
    """
    Main entry point for the 'ak' CLI tool.

    This group command initializes the logger, configuration, and AWS profile settings,
    passing them via the Click context to subcommands.

    :param ctx: Click context.
    :param debug: Flag to enable debug logging.
    :param aws_profile: AWS profile name to be used.
    """
    ctx.ensure_object(dict)
    logger = setup_logger("ak", debug=debug)
    config = AKConfig()
    ctx.obj["logger"] = logger
    ctx.obj["config"] = config
    ctx.obj["aws_profile"] = aws_profile


@ak.command("l", help="AWS MFA login. Provide the MFA code.")
@click.argument("mfa_code", required=True)
@click.pass_context
def login_command(ctx, mfa_code):
    """
    Perform AWS MFA login.

    Uses the specified (or default) AWS profile to fetch an MFA-based STS session token.
    The command prints an export statement (e.g., ``export AWS_PROFILE=...``) so that the
    calling shell can update its environment accordingly.

    :param ctx: Click context containing the logger and configuration.
    :param mfa_code: The MFA code provided by the user.
    :type mfa_code: str
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    aws_profile_name = ctx.obj["aws_profile"]

    if aws_profile_name is None:
        aws_profile_name = config.default_aws_profile

    aws_mgr = AWSManager(config, logger, aws_profile_name=aws_profile_name)

    try:
        click.echo(aws_mgr.mfa_login(mfa_code))
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


@ak.command("c", help="Switch to a specific kubeconfig by name.")
@click.argument("kube_name", required=True, shell_complete=complete_kube_name)
@click.pass_context
def switch_kubeconfig(ctx, kube_name):
    """
    Switch to a specific Kubernetes configuration.

    Copies the specified kubeconfig to a temporary file (refreshing tokens if necessary)
    and prints an export statement (e.g., ``export KUBECONFIG=...``) so the calling shell
    can update its environment.

    :param ctx: Click context containing the logger and configuration.
    :param kube_name: The name of the kubeconfig to switch to.
    :type kube_name: str
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    kube_mgr = KubeManager(config, logger)

    try:
        export_line = kube_mgr.switch_config(kube_name)
        click.echo(export_line)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


@ak.command("x", help="Switch context within the current KUBECONFIG.")
@click.argument("context_name", required=True, shell_complete=complete_context_name)
@click.pass_context
def switch_context(ctx, context_name):
    """
    Switch the current Kubernetes context.

    Updates the active context in the existing temporary kubeconfig and adjusts the
    shell prompt (PS1) accordingly.

    :param ctx: Click context containing the logger and configuration.
    :param context_name: The Kubernetes context name to switch to.
    :type context_name: str
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    kube_mgr = KubeManager(config, logger)

    try:
        export_line = kube_mgr.switch_context(context_name)
        click.echo(export_line)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


@ak.command("r", help="Force token refresh for the current KUBECONFIG.")
@click.pass_context
def force_refresh(ctx):
    """
    Force a refresh of the Kubernetes API token.

    This command touches the token timestamp so that a new token will be generated on the
    next use of kubectl.

    :param ctx: Click context containing the logger and configuration.
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    kube_mgr = KubeManager(config, logger)

    try:
        kube_mgr.force_refresh()
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


def get_shell_mode(shell):
    """
    Determine the Click completion mode for the given shell.

    :param shell: The shell name (e.g., "bash", "zsh", "fish", "powershell").
    :type shell: str
    :return: The Click completion mode corresponding to the shell.
    :rtype: str
    :raises ValueError: If the shell is unsupported.
    """
    if shell == "bash":
        return "bash_source"
    elif shell == "zsh":
        return "zsh_source"
    elif shell == "fish":
        return "fish_source"
    elif shell == "powershell":
        return "powershell_source"
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def get_official_completion(mode):
    """
    Retrieve the official Click-generated shell completion script.

    Executes a subprocess call with the environment variable ``_AK_COMPLETE`` set to the
    specified mode and returns the resulting completion script.

    :param mode: The shell completion mode.
    :type mode: str
    :return: The shell completion script.
    :rtype: str
    :raises subprocess.CalledProcessError: If the subprocess call fails.
    """
    try:
        result = subprocess.run(
            ["env", f"_AK_COMPLETE={mode}", "ak"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to retrieve completion script: {e.stderr}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


def generate_bash_zsh_wrapper(shell):
    """
    Generate a custom wrapper function for Bash or Zsh.

    The wrapper executes the 'ak' binary and evaluates lines that begin with
    ``export`` or ``if`` to update the shell's environment.

    :param shell: The shell type ("bash" or "zsh").
    :type shell: str
    :return: A string containing the custom wrapper script.
    :rtype: str
    """
    return f"""
# Wrapper function for 'ak': executes the binary and evaluates 'export' and 'if' lines
function ak() {{
    local output
    output=$(command ak "$@") || return 1
    while IFS= read -r line; do
        if [[ "$line" =~ ^(export|if)[[:space:]] ]] ; then
            eval "$line"
        else
            echo "$line"
        fi
    done <<< "$output"
}}
echo "Loaded {shell} completion and function wrapper for 'ak'."
"""


def generate_fish_wrapper():
    """
    Generate a custom wrapper function for the Fish shell.

    The wrapper executes the 'ak' command and evaluates lines that begin with ``export``
    or ``if``, ensuring environment variables are updated correctly.

    :return: A string containing the Fish shell wrapper script.
    :rtype: str
    """
    return r"""
function ak --wraps command ak
    set -l output (command ak $argv ^/dev/null)
    for line in $output
        if string match --quiet --regex '^(export|if) ' "$line"
            eval $line
        else
            echo $line
        end
    end
end
echo "Loaded Fish completion and function wrapper for 'ak'."
"""


def generate_powershell_wrapper():
    """
    Generate a custom wrapper function for PowerShell.

    The wrapper executes the 'ak' command and evaluates lines that begin with ``export``
    (after stripping the export keyword) so that environment variables are updated.

    :return: A string containing the PowerShell wrapper script.
    :rtype: str
    """
    return r"""
function ak {
    $output = & ak @args
    foreach ($line in $output) {
        if ($line -match '^(export|if)\s') {
            Invoke-Expression ($line -replace '^export\s+', '')
        } else {
            Write-Output $line
        }
    }
}
Write-Host "Loaded PowerShell completion and function wrapper for 'ak'."
"""


def generate_custom_wrapper(shell):
    """
    Generate a shell-specific custom function wrapper.

    Dispatches the wrapper generation to the appropriate function based on the shell.

    :param shell: The shell name ("bash", "zsh", "fish", or "powershell").
    :type shell: str
    :return: A string containing the custom wrapper script for the specified shell.
    :rtype: str
    """
    if shell in ["bash", "zsh"]:
        return generate_bash_zsh_wrapper(shell)
    elif shell == "fish":
        return generate_fish_wrapper()
    elif shell == "powershell":
        return generate_powershell_wrapper()
    else:
        click.echo(f"Unsupported shell: {shell}", err=True)
        sys.exit(1)


@ak.command(
    "completion",
    help="Generate a shell completion script and custom function wrapper.",
)
@click.argument(
    "shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]), default="bash"
)
def completion_cmd(shell):
    """
    Generate a shell completion script and custom function wrapper.

    This command prints the official Click-generated shell completion script for the
    chosen shell, then appends a shell-specific wrapper function that evaluates lines
    starting with ``export`` and ``if``.

    :param shell: The shell type for which to generate the completion script.
    :type shell: str
    """
    try:
        mode = get_shell_mode(shell)
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    official_script = get_official_completion(mode)
    custom_wrapper = generate_custom_wrapper(shell)

    click.echo(official_script)
    click.echo(custom_wrapper)


def main():
    """
    Entry point for the 'ak' CLI tool.

    Invokes the Click command group.
    """
    ak()


if __name__ == "__main__":
    main()
