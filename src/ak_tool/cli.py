#!/usr/bin/env python
"""CLI entry point for the 'ak' tool.

This module provides the command-line interface for the 'ak' tool, which consolidates
AWS MFA login, Kubernetes context switching, and Kubernetes API token refreshing into
one simple CLI tool. It also includes functionality to print out the current version
when called with --version.
"""

import sys
import os
import subprocess
import click
from click.shell_completion import CompletionItem
from ak_tool.config import AKConfig
from ak_tool.logger import setup_logger
from ak_tool.core import AWSManager, KubeManager
from ak_tool import __version__


def complete_aws_profile(ctx, param, incomplete):
    """Return a list of AWS profile names matching the incomplete text.

    Retrieves AWS profile names from configuration sections that start with
    `aws.` and returns those that begin with the provided incomplete string.

    Args:
        ctx (click.Context): Click context.
        param (click.Parameter): Click parameter.
        incomplete (str): Incomplete text typed by the user.

    Returns:
        list[CompletionItem]: A list of CompletionItem objects with matching AWS profile names.
    """
    config = AKConfig()
    profiles = []
    for section in config._cp.sections():
        if section.startswith("aws."):
            profile_name = section[4:]  # e.g. "aws.home" -> "home"
            if profile_name.startswith(incomplete):
                profiles.append(CompletionItem(profile_name))
    return profiles


def complete_kubeconfig_name(ctx, param, incomplete):
    """Return a list of kubeconfig filenames matching the incomplete text.

    Scans the directory specified by the configuration for kubeconfigs and returns
    filenames that start with the provided incomplete string.

    Args:
        ctx (click.Context): Click context.
        param (click.Parameter): Click parameter.
        incomplete (str): Incomplete text typed by the user.

    Returns:
        list[CompletionItem]: A list of CompletionItem objects with matching kubeconfig filenames.
    """
    config = AKConfig()
    kubeconfigs_dir = config.kube_configs_dir
    kubeconfigs_dir = os.path.expanduser(kubeconfigs_dir)

    if not os.path.isdir(kubeconfigs_dir):
        return []

    items = []
    for fname in os.listdir(kubeconfigs_dir):
        if fname.startswith(incomplete):
            items.append(CompletionItem(fname))
    return items


def complete_context_name(ctx, param, incomplete):
    """Return a list of Kubernetes context names matching the incomplete text.

    Executes `kubectl config get-contexts -o name` to retrieve context names,
    then filters and returns those that start with the provided incomplete string.

    Args:
        ctx (click.Context): Click context.
        param (click.Parameter): Click parameter.
        incomplete (str): Incomplete text typed by the user.

    Returns:
        list[CompletionItem]: A list of CompletionItem objects with matching Kubernetes context names.
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


@click.version_option(version=__version__, prog_name="ak")
@click.group(
    short_help="A unified CLI for AWS MFA logins and Kubernetes context management.",
    help=(
        "ak (Access Kubernetes) consolidates AWS MFA login, Kubernetes context switching, "
        "and on-demand token refresh into a single CLI tool.\n\n"
        "For more details, see the official documentation or run 'ak COMMAND --help' "
        "to learn about each command."
    )
)
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.option(
    "--aws-profile",
    help="Name of AWS sub-profile section (e.g., 'company', 'home').",
    shell_complete=complete_aws_profile,
)
@click.pass_context
def ak(ctx, debug, aws_profile):
    """Main entry point for the 'ak' CLI tool.

    This group command initializes the logger, configuration, and AWS profile settings,
    passing them via the Click context to subcommands.

    Additionally, when invoked with the `--version` flag, the current version of the tool
    will be printed to the console.

    Args:
        ctx (click.Context): The Click context containing the logger and configuration.
        debug (bool): Flag to enable debug logging.
        aws_profile (str): AWS profile name to be used.
    """
    ctx.ensure_object(dict)
    logger = setup_logger("ak", debug=debug)
    config = AKConfig()
    ctx.obj["logger"] = logger
    ctx.obj["config"] = config
    ctx.obj["aws_profile"] = aws_profile


@ak.command(
    "l",
    short_help="Perform AWS MFA login with a one-time code.",
    help=(
        "Use an AWS MFA one-time code (e.g., from Authenticator or a hardware token) to "
        "generate short-lived AWS credentials under the corresponding authenticated profile. "
        "Prints an 'export' statement to update the calling shell environment.\n\n"
        "Example: ak l 123456"
    )
)
@click.argument("mfa_code", required=True)
@click.pass_context
def login_command(ctx, mfa_code):
    """Perform AWS MFA login.

    Uses the specified (or default) AWS profile to fetch an MFA-based STS session token.
    The command prints an export statement (e.g., `export AWS_PROFILE=...`) so that the
    calling shell can update its environment accordingly.

    Args:
        ctx (click.Context): The Click context containing the logger and configuration.
        mfa_code (str): The MFA code provided by the user.
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


@ak.command(
    "c",
    short_help="Switch to a named kubeconfig.",
    help=(
        "Copies the specified kubeconfig to a temporary location, refreshing tokens if "
        "necessary, and prints an 'export KUBECONFIG=...' statement. This allows you to "
        "quickly switch between different Kubernetes clusters.\n\n"
        "Example: ak c dev"
    )
)
@click.argument("kubeconfig_name", required=True, shell_complete=complete_kubeconfig_name)
@click.pass_context
def switch_kubeconfig(ctx, kubeconfig_name):
    """Switch to a specific Kubernetes configuration.

    Copies the specified kubeconfig to a temporary file (refreshing tokens if necessary)
    and prints an export statement (e.g., `export KUBECONFIG=...`) so the calling shell
    can update its environment.

    Args:
        ctx (click.Context): The Click context containing the logger and configuration.
        kubeconfig_name (str): The name of the kubeconfig to switch to.
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    kube_mgr = KubeManager(config, logger)

    try:
        export_line = kube_mgr.switch_config(kubeconfig_name)
        click.echo(export_line)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


@ak.command(
    "x",
    short_help="Switch context within the active kubeconfig.",
    help=(
        "Select a different context in the existing kubeconfig, then update your shell prompt "
        "accordingly. Great for switching namespaces or cluster contexts without changing "
        "the underlying kubeconfig file.\n\n"
        "Example: ak x kube-system"
    )
)
@click.argument("context_name", required=True, shell_complete=complete_context_name)
@click.pass_context
def switch_context(ctx, context_name):
    """Switch the current Kubernetes context.

    Updates the active context in the existing temporary kubeconfig and adjusts the
    shell prompt (PS1) accordingly.

    Args:
        ctx (click.Context): The Click context containing the logger and configuration.
        context_name (str): The Kubernetes context name to switch to.
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


@ak.command(
    "r",
    short_help="Force a Kubernetes API token refresh.",
    help=(
        "Refresh Kubernetes tokens in the current (or specified) kubeconfig file, ensuring "
        "your local environment remains authenticated. Useful if the token expires or you "
        "just want to proactively refresh.\n\n"
        "Example: ak r --kubeconfig dev"
    )
)
@click.option(
    "--kubeconfig",
    "-k",
    default="",
    help="Name of kubeconfig file to refresh. Use 'all' to refresh all kubeconfigs.",
    shell_complete=complete_kubeconfig_name,
)
@click.pass_context
def force_refresh(ctx, kubeconfig):
    """Force a refresh of the Kubernetes API token.

    This command refreshes all the static Kubernetes API tokens for the current
    kubeconfig, or for a specified kubeconfig if provided.

    Args:
        ctx (click.Context): The Click context containing the logger and configuration.
        kubeconfig (str): Name of kubeconfig file to refresh. Use 'all' to refresh all kubeconfigs.
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    kube_mgr = KubeManager(config, logger)

    try:
        kube_mgr.force_refresh(kubeconfig)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


def get_shell_mode(shell):
    """Determine the Click completion mode for the given shell.

    Args:
        shell (str): The shell name (e.g., "bash", "zsh", or "fish").

    Returns:
        str: The Click completion mode corresponding to the shell.

    Raises:
        ValueError: If the shell is unsupported.
    """
    if shell == "bash":
        return "bash_source"
    elif shell == "zsh":
        return "zsh_source"
    elif shell == "fish":
        return "fish_source"
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def get_official_completion(mode):
    """Retrieve the official Click-generated shell completion script.

    Executes a subprocess call with the environment variable `_AK_COMPLETE`
    set to the specified mode and returns the resulting completion script.

    Args:
        mode (str): The shell completion mode.

    Returns:
        str: The shell completion script.

    Raises:
        subprocess.CalledProcessError: If the subprocess call fails.
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
    """Generate a custom wrapper function for Bash or Zsh.

    The wrapper executes the 'ak' binary and evaluates lines that begin with
    the `>>>` prefix to update the shell's environment and prompt.

    Args:
        shell (str): The shell type ("bash" or "zsh").

    Returns:
        str: A string containing the custom wrapper script.
    """
    return f"""
# Wrapper function for 'ak': executes the binary and evaluates lines that start with '>>>' prefix
function ak() {{
    # Local variables
    local output
    local script=""
    
    # Run the actual 'ak' command, capturing its output
    output=$(command ak "$@") || return 1
    
    # Read each line of output
    while IFS= read -r line; do
        # If the line begins with >>>, remove the prefix and accumulate
        if [[ $line == ">>>"* ]]; then
            line="${{line#>>>}}"
            script+="$line
"
        else
            echo "$line"
        fi
    done <<< "$output"
    
    # Evaluate the accumulated lines at once
    eval "$script"
}}
"""


def generate_bash_zsh_prompt_script() -> str:
    """Generate a one-off script for Bash/Zsh that defines and sets a colorful prompt
    showing user@host, directory, Git branch, and Kube context.

    Returns:
        str: The script for setting a colorful prompt in Bash/Zsh.
    """
    return r"""
# Define a function to set a new colorful prompt
function ak_prompt {
    # Username@Host in bold green
    local __user_and_host="\[\033[01;32m\]\u@\h"

    # Current directory in bold blue
    local __cur_location="\[\033[01;34m\]\w"

    # Reset color
    local __reset_color="\[\033[00m\]"

    # Git branch in red
    local __git_branch_color="\[\033[31m\]"
    local __git_branch='`git branch --show-current 2>/dev/null | sed -E "s/(.*)/\1\\\[\\\033[00m\\\],/"`'

    # Kubeconfig in purple
    local __kubeconfig_color="\[\033[35m\]"
    local __kubeconfig='`{ [ -z "$KUBECONFIG" ] && echo '-' || basename "$KUBECONFIG" | sed 's/-temp$//'; }`'

    # Kube context in cyan (if any)
    local __kube_context_color="\[\033[36m\]"
    local __kube_context='`{ c="$(kubectl config current-context 2>/dev/null)"; [ -z "$c" ] || [ -z "$KUBECONFIG" ] && echo '-' || echo "$c"; }`'

    # Prompt tail in purple
    local __prompt_tail="\$"

    # Compose the final PS1
    export PS1="${__user_and_host} ${__cur_location} "\
"${__reset_color}("\
"${__git_branch_color}${__git_branch}"\
"${__kubeconfig_color}${__kubeconfig}"\
"${__reset_color}/"\
"${__kube_context_color}${__kube_context}"\
"${__reset_color})"\
"${__prompt_tail}${__reset_color} "
}
ak_prompt
"""


def generate_fish_wrapper():
    """Generate a custom wrapper function for the Fish shell.

    The wrapper executes the 'ak' command and accumulates lines that begin with the
    `>>>` prefix into a single string, then evaluates them all at once.

    Returns:
        str: The custom wrapper function script for the Fish shell.
    """
    return r"""
function ak --wraps=command ak
    set -l output (command ak $argv)
    set -l script ""
    
    for line in $output
        if test (string sub -l 3 $line) = ">>>"
            set -l stripped_line (string sub --start=3 $line)
            if test -z "$script"
                set script "$stripped_line"
            else
                set script "$script
$stripped_line"
            end
        else
            echo $line
        end
    end
    
    if not test -z "$script"
        eval "$script"
    end
end
"""


def generate_fish_prompt_script() -> str:
    """Generate a one-off script for Fish that defines a new fish_prompt function
    showing user@host, directory, Git branch, and Kube context in color.

    Returns:
        str: The Fish prompt script.
    """
    return r"""
function fish_prompt
    # 1. user@host in bold green
    set_color green --bold
    echo -n (whoami)"@"(hostname -s)" "

    # 2. current directory in bold blue
    set_color blue --bold
    echo -n (pwd)" "

    # 3. reset color, then print "("
    set_color normal
    echo -n "("

    # 4. Git branch in red (with trailing comma if non-empty)
    set branch (git branch --show-current 2>/dev/null)
    if test -n "$branch"
        set_color red
        echo -n $branch
        set_color normal
        echo -n ","
    end

    # 5. Kubeconfig in purple or '-' if empty
    set kubecfg ""
    if test -z "$KUBECONFIG"
        set kubecfg "-"
    else
        set tmp (basename "$KUBECONFIG")
        set tmp (string replace -r '-temp$' '' -- $tmp)
        set kubecfg $tmp
    end

    set_color magenta
    echo -n $kubecfg

    # 6. Print a slash in default color
    set_color normal
    echo -n "/"

    # 7. Kube context in cyan or '-' if empty (or if $KUBECONFIG is empty)
    set ctx (kubectl config current-context 2>/dev/null)
    if test -z "$ctx" -o -z "$KUBECONFIG"
        set ctx "-"
    end

    set_color cyan
    echo -n $ctx

    # 8. close parentheses
    set_color normal
    echo -n ")"

    # 9. final prompt symbol in purple
    set_color magenta
    echo -n "$ "

    # 10. reset color
    set_color normal
end
"""


def generate_custom_wrapper(shell):
    """Generate a shell-specific custom function wrapper.

    Dispatches the wrapper generation to the appropriate function based on the shell.

    Args:
        shell (str): The shell name ("bash", "zsh", or "fish").

    Returns:
        str: A string containing the custom wrapper script for the specified shell.

    Raises:
        SystemExit: Prints an error and exits if the shell is unsupported.
    """
    if shell in ["bash", "zsh"]:
        return generate_bash_zsh_wrapper(shell)
    elif shell == "fish":
        return generate_fish_wrapper()
    else:
        click.echo(f"Unsupported shell: {shell}", err=True)
        sys.exit(1)


def generate_prompt_script(shell: str) -> str:
    """Return a one-off script that sets a colorized prompt displaying user@host,
    current directory, Git branch, and Kube context for the specified shell.

    Args:
        shell (str): The shell name ("bash", "zsh", or "fish").

    Returns:
        str: The prompt script for the specified shell.
    """
    if shell in ["bash", "zsh"]:
        return generate_bash_zsh_prompt_script()
    elif shell == "fish":
        return generate_fish_prompt_script()
    else:
        return ""


@ak.command(
    "completion",
    short_help="Generate a shell completion script for bash, zsh, or fish.",
    help=(
        "Generates an official Click completion script for your chosen shell (bash, zsh, or fish) "
        "and a custom wrapper that updates environment variables. You can source this script for "
        "interactive tab-completion.\n\n"
        "Example:\n  eval \"$(ak completion bash)\""
    )
)
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]), default="bash")
def completion_cmd(shell):
    """Generate a shell completion script and custom function wrapper.

    This command prints the official Click-generated shell completion script for the
    chosen shell, then appends a shell-specific wrapper function that adjusts
    environment variables and prompt.

    Args:
        shell (str): The shell type ("bash", "zsh", or "fish").
    """
    try:
        mode = get_shell_mode(shell)
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    official_script = get_official_completion(mode)
    custom_wrapper = generate_custom_wrapper(shell)
    prompt_script = generate_prompt_script(shell)

    click.echo(official_script)
    click.echo(custom_wrapper)
    click.echo(prompt_script)


def main():
    """Entry point for the 'ak' CLI tool.

    Invokes the Click command group.
    """
    ak()


if __name__ == "__main__":
    main()
