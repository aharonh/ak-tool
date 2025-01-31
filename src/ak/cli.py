import sys
import os
import subprocess
import click
from click.shell_completion import CompletionItem
from ak.config import AKConfig
from ak.logger import setup_logger
from ak.core import AWSManager, KubeManager


#
# Shell-complete helper for --aws-profile
#
def complete_aws_profile(ctx, param, incomplete):
    """
    Return a list of all 'aws.<profile>' sections from config that match
    the current 'incomplete' user-typed text.
    """
    config = AKConfig()
    profiles = []
    for section in config._cp.sections():
        if section.startswith("aws."):
            profile_name = section[4:]  # e.g. "aws.home" -> "home"
            if profile_name.startswith(incomplete):
                profiles.append(CompletionItem(profile_name))
    return profiles


#
# Shell-complete for <kube_name> in 'ak c'
#
def complete_kube_name(ctx, param, incomplete):
    """
    Returns matching filenames from ~/.kubeconfigs that start with 'incomplete'.
    """
    config = AKConfig()
    kube_dir = config.kube_configs_dir  # or fallback to '~/.kubeconfigs'
    kube_dir = os.path.expanduser(kube_dir)

    if not os.path.isdir(kube_dir):
        return []

    items = []
    for fname in os.listdir(kube_dir):
        # If user typed partial text "de", match "dev", etc.
        if fname.startswith(incomplete):
            items.append(CompletionItem(fname))
    return items


#
# Shell-complete for <context_name> in 'ak x'
#
def complete_context_name(ctx, param, incomplete):
    """
    Uses 'kubectl config get-contexts -o name' to list contexts.
    Filters by 'incomplete'.
    """
    try:
        import subprocess

        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.split()
    except Exception:
        # If kubectl not installed or error running command
        return []

    items = []
    for line in lines:
        if line.startswith(incomplete):
            items.append(CompletionItem(line))
    return items


#
# The main Click group (with global options)
#
@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.option(
    "--aws-profile",
    help="Name of AWS sub-profile section, e.g. 'company', 'home'.",
    shell_complete=complete_aws_profile,
)
@click.pass_context
def ak(ctx, debug, aws_profile):
    ctx.ensure_object(dict)
    logger = setup_logger("ak", debug=debug)
    config = AKConfig()
    ctx.obj["logger"] = logger
    ctx.obj["config"] = config
    ctx.obj["aws_profile"] = aws_profile


#
# 'l' subcommand: AWS MFA login
#
@ak.command("l", help="AWS MFA login. Provide the MFA code.")
@click.argument("mfa_code", required=True)
@click.pass_context
def login_command(ctx, mfa_code):
    """
    ak l <mfa_code>

    Uses the specified (or default) AWS profile to fetch an MFA-based STS session token.
    Prints 'export AWS_PROFILE=...' so the calling shell can eval it.
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    aws_profile_name = ctx.obj["aws_profile"]

    # if not provided, use the default profile
    if aws_profile_name is None:
        aws_profile_name = config.default_aws_profile

    aws_mgr = AWSManager(config, logger, aws_profile_name=aws_profile_name)

    try:
        click.echo(aws_mgr.mfa_login(mfa_code))
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


#
# 'c' subcommand: Switch Kubeconfig
#
@ak.command("c", help="Switch to a specific kubeconfig by name.")
@click.argument("kube_name", required=True, shell_complete=complete_kube_name)
@click.pass_context
def switch_kubeconfig(ctx, kube_name):
    """
    ak c <kube_name>

    Copies the specified kubeconfig to a temp file, refreshing tokens if needed.
    Prints 'export KUBECONFIG=...' so the calling shell can eval it.
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


#
# 'x' subcommand: Switch Context
#
@ak.command("x", help="Switch context within the current KUBECONFIG.")
@click.argument("context_name", required=True, shell_complete=complete_context_name)
@click.pass_context
def switch_context(ctx, context_name):
    """
    ak x <context_name>

    Switches the current context in the existing (temp) kubeconfig,
    and updates the shell prompt (PS1).
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


#
# 'r' subcommand: Force Refresh
#
@ak.command(
    "r",
    help="Force token refresh for the current KUBECONFIG.",
)
@click.pass_context
def force_refresh(ctx):
    """
    ak r

    Touches the token timestamp so that new tokens are generated
    on the next kubectl usage.
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
    """Determine the Click completion mode for the given shell."""
    if shell == "bash":
        return "bash_source"
    elif shell == "zsh":
        return "zsh_source"
    elif shell == "fish":
        return "fish_source"
    elif shell == "powershell":
        return "powershell_source"
    else:
        # This case is guarded by Click's argument choice, so unreachable under
        # normal use
        raise ValueError(f"Unsupported shell: {shell}")


def get_official_completion(mode):
    """Retrieve the official Click completion script for the given mode."""
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
    """Generate custom wrapper function for Bash or Zsh."""
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
    """Generate custom wrapper function for Fish."""
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
    """Generate custom wrapper function for PowerShell."""
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
    """Generate the shell-specific custom function wrapper."""
    if shell in ["bash", "zsh"]:
        return generate_bash_zsh_wrapper(shell)
    elif shell == "fish":
        return generate_fish_wrapper()
    elif shell == "powershell":
        return generate_powershell_wrapper()
    else:
        # Guarded by Click's argument choice
        click.echo(f"Unsupported shell: {shell}", err=True)
        sys.exit(1)


#
# 'completion' subcommand: Generate shell completion script
#
@ak.command(
    "completion",
    help=("Generate a shell completion script and custom function wrapper."),
)
@click.argument(
    "shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]), default="bash"
)
def completion_cmd(shell):
    """
    ak completion [bash|zsh|fish|powershell]

    1) Print the official Click-generated completion script for the chosen shell.
    2) Append a shell-specific wrapper function that evaluates 'export' and 'if' lines.
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


#
# Final entrypoint
#
def main():
    ak()


if __name__ == "__main__":
    main()
