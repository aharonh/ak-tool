# ak tool

**ak** tool (**a**ccess **k**ubernetes) is a unified CLI tool that simplifies AWS MFA logins, Kubernetes context switching, and Kubernetes API token refreshing. Designed for engineers managing multiple Kubernetes clusters across different AWS accounts, **ak** streamlines daily authentication and environment management—especially when using OpenID Connect SSO, MFA, or other secure authentication methods.

---

## Table of Contents

- [ak tool](#ak-tool)
  - [Table of Contents](#table-of-contents)
  - [Quick Start](#quick-start)
    - [1. Install](#1-install)
    - [2. Source the Completion Script](#2-source-the-completion-script)
    - [3. Run `ak` Commands](#3-run-ak-commands)
    - [4. Prompt \& Environment Variables](#4-prompt--environment-variables)
  - [Introduction](#introduction)
  - [Features](#features)
    - [Streamlined AWS MFA Authentication](#streamlined-aws-mfa-authentication)
      - [How It Works](#how-it-works)
      - [Configuration Breakdown](#configuration-breakdown)
      - [AWS CLI Configuration](#aws-cli-configuration)
      - [How `ak` Updates Credentials](#how-ak-updates-credentials)
    - [Streamlined Kubernetes API Authentication](#streamlined-kubernetes-api-authentication)
      - [How It Works](#how-it-works-1)
      - [Configuration Breakdown](#configuration-breakdown-1)
      - [AWS CLI Configuration](#aws-cli-configuration-1)
      - [The kubeconfig File](#the-kubeconfig-file)
    - [Multiple Kubeconfigs \& Namespaces](#multiple-kubeconfigs--namespaces)
    - [Automatic or On-Demand Token Refresh](#automatic-or-on-demand-token-refresh)
    - [Kubernetes \& AWS Profile Synchronization](#kubernetes--aws-profile-synchronization)
    - [Completion](#completion)
  - [Command Line Parameters](#command-line-parameters)
    - [Commands and general options](#commands-and-general-options)
    - [Set configuration file command](#set-configuration-file-command)
    - [Set current context command](#set-current-context-command)
    - [Refresh token(s) command](#refresh-tokens-command)
    - [Completion command](#completion-command)
  - [Configuration](#configuration)
  - [Testing](#testing)
    - [Run Tests with Pytest Directly](#run-tests-with-pytest-directly)
    - [Using Make](#using-make)
    - [Coverage Reports](#coverage-reports)
  - [For further reference](#for-further-reference)
  - [Final Notes](#final-notes)

---

## Quick Start

### 1. Install 

```bash
pip3 install ak-tool
```

**Using a virtual environment:**

Assuming you have git, python3 and make installed on your system:

```bash
git clone https://github.com/aharonh/ak-tool.git
cd ak
python3 -m venv .venv
source .venv/bin/activate
make install
```

### 2. Source the Completion Script

```bash
eval "$(ak completion bash)"
```

### 3. Run `ak` Commands

- **AWS Login with MFA Code:**

  ```bash
  ak l 123456
  ```

- **Switch to a Particular Kubeconfig:**

  ```bash
  ak c dev
  ```

- **Switch to a Named Context:**

  ```bash
  ak x kube-system
  ```

### 4. Prompt & Environment Variables

- After running `ak c <kubeconfig>` or `ak x <context>`, your shell prompt (`PS1`) updates to reflect the active context.
- The `AWS_PROFILE` environment variable is automatically set to match the AWS account linked to the new context.
- The `KUBECONFIG` environment variable is updated to point to the correct kubeconfig file.

---

## Introduction

Managing multiple AWS accounts and Kubernetes clusters can be complex. **ak** minimizes that complexity by:

- Handling AWS MFA tokens and short-lived Kubernetes API tokens.
- Automating token refreshes.
- Providing a single interface for switching contexts across environments.

---

## Features

### Streamlined AWS MFA Authentication

**ak** simplifies the process of AWS MFA authentication and token management. In secure environments where MFA and SSO are required, **ak** reduces the daily authentication steps to a single command.

#### How It Works

- **Dual-Profile Model:**  
  - **Original Profile:** Used for initial MFA authentication with AWS.
  - **Authenticated Profile:** Stores temporary credentials after MFA validation.

Running:

```bash
ak l 123456
```

performs the following steps:

1. Authenticates using the **original profile**.
2. Retrieves a temporary AWS STS session token.
3. Writes new credentials under the **authenticated profile** in your AWS credentials file.
4. Switches AWS authentication to the **authenticated profile**.

#### Configuration Breakdown

Key configuration options:

- `credentials_file`: Path to your AWS credentials file.
- `token_validity_seconds`: Duration (in seconds) for temporary credentials (e.g., 43200 seconds).
- `default_profile`: Default AWS profile when `--aws-profile` is not specified.
- Per-account settings (`[aws.<profile_name>]`):
  - `original_profile`: AWS profile for initial MFA.
  - `authenticated_profile`: AWS profile to store temporary credentials.
  - `mfa_serial`: ARN of the MFA device.

Example configuration:

```ini
[aws]
credentials_file = /home/user/.aws/credentials
token_validity_seconds = 43200
default_profile = company

[aws.company]
original_profile = company-root
authenticated_profile = company-root-mfa
mfa_serial = arn:aws:iam::3453453454345:mfa/yubikey4

[aws.home]
original_profile = home-systems
authenticated_profile = home-systems-mfa
mfa_serial = arn:aws:iam::262626262626:mfa/yubikey4
```

#### AWS CLI Configuration

Ensure your AWS CLI is correctly configured. Example for the AWS config file:

```ini
[profile company-root]
region = us-east-1
output = json

[profile company-root-mfa]
region = us-east-1
output = json
```

And the corresponding AWS credentials file:

```ini
[company-root]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[company-root-mfa]
aws_access_key_id = ASIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws_session_token = FQoGZXIvYXdzEJr//////////wEaDIN
```

#### How `ak` Updates Credentials

When you run:

```bash
ak l 123456
```

**ak**:

1. Uses the **original profile** for MFA validation.
2. Retrieves and stores a temporary STS session token under the **authenticated profile**.
3. Updates the credentials in your `~/.aws/credentials` file, ensuring you always have valid credentials.

---

### Streamlined Kubernetes API Authentication

Managing Kubernetes API tokens—especially for kOps-based clusters—can be cumbersome. **ak** caches and refreshes these tokens to speed up your workflow.

#### How It Works

- **Token Caching:**  
  **ak** caches the Kubernetes API token in a temporary file.
- **Automatic Refresh:**  
  The token is refreshed automatically upon expiration.
- **Improved Performance:**  
  This avoids the overhead of generating a new token with each `kubectl` command.

#### Configuration Breakdown

Configuration options for Kubernetes:

- `configs_dir`: Directory containing your kubeconfig files.
- `temp_dir`: Directory for storing temporary Kubernetes tokens.
- `token_validity_seconds`: Duration (in seconds) for which the Kubernetes token is valid.
- `default_config`: Default kubeconfig used with the `ak l` command.

Example configuration:

```ini
[kube]
configs_dir = /home/user/.kubeconfigs
temp_dir = /home/user/.kubeconfigs_temp
token_validity_seconds = 900
default_config = dev
```

#### AWS CLI Configuration

When working with multiple clusters across AWS accounts, you may need additional AWS profiles. For example:

```ini
[profile company-dev-access]
region = us-east-1
output = json
role_arn = arn:aws:iam::11111111111111:role/admin
source_profile = company-root-mfa
role_session_name = your.username

[profile company-prod-access]
region = eu-central-1
output = json
role_arn = arn:aws:iam::22222222222222:role/admin
source_profile = company-root-mfa
role_session_name = your.username
```

**ak** automatically sets the correct `AWS_PROFILE` based on the kubeconfig context.

#### The kubeconfig File

**ak** scans your kubeconfig file for users with an `exec` section using `aws-iam-authenticator`. It generates a temporary kubeconfig file that replaces the `aws-iam-authenticator` command entries with a cached token.

Example kubeconfig entry (before):

```yaml
users:
- name: aws-user-dev
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      args:
      - token
      - -i
      - dev.company.com
      command: /home/user/bin/aws-iam-authenticator
      env:
      - name: AWS_PROFILE
        value: company-dev-access
      interactiveMode: IfAvailable
      provideClusterInfo: false
```

The entry is replaced with:

```yaml
- name: aws-user-dev
  user:
    token: k8s-aws-v1.aHR0cHM6Ly9zdHMuYW1hem9uYXdzLmNvbS8_QWN0aW9uPUdldENhbGxlcklkZW50aXR5JlZlcnNpb249MjAxMS
    # additional fields...
```

---

### Multiple Kubeconfigs & Namespaces

- **Switch Kubeconfigs:**  
  Easily switch between different clusters (e.g., dev, test, prod):

  ```bash
  ak c prod
  ```

- **Switch Namespaces:**  
  Change between namespace contexts within a single cluster:

  ```bash
  ak x kube-system
  ```

- **Visual Feedback:**  
  The active context is displayed in your shell prompt (e.g., `(dev-kube-system) $`).

---

### Automatic or On-Demand Token Refresh

- **Automatic Refresh:**  
  When the Kubernetes API token expires but the AWS session token remains valid, **ak** automatically refreshes the token.
- **Manual Refresh:**  
  Force a token refresh with:

  ```bash
  ak r
  ```

---

### Kubernetes & AWS Profile Synchronization

Each kubeconfig context is associated with an AWS profile. When you switch contexts using:

```bash
ak x <context>
```

**ak** exports the appropriate `AWS_PROFILE` so that all your AWS CLI commands use the correct account credentials.

---

### Completion

**ak** supports tab-completion for Bash, Zsh, and Fish. To enable completion for Bash, run:

```bash
eval "$(ak completion bash)"
```

For persistent Bash completion, install the completion script:

```bash
ak completion bash | sudo tee /etc/bash_completion.d/ak
. /etc/bash_completion.d/ak
```

---

## Command Line Parameters

The ak CLI tool provides general help for the tool, and help for each of the supported commands. 

Below are descriptions of the command line paramters as they are presented by the tool.

### Commands and general options

```bash
ak --help

Usage: ak [OPTIONS] COMMAND [ARGS]...

  ak (Access Kubernetes) consolidates AWS MFA login, Kubernetes context
  switching, and on-demand token refresh into a single CLI tool.

  For more details, see the official documentation or run 'ak COMMAND --help'
  to learn about each command.

Options:
  --debug             Enable debug logging.
  --aws-profile TEXT  Name of AWS sub-profile section (e.g., 'company',
                      'home').
  --version           Show the version and exit.
  --help              Show this message and exit.

Commands:
  c           Switch to a named kubeconfig.
  completion  Generate a shell completion script for bash, zsh, or fish.
  l           Perform AWS MFA login with a one-time code.
  r           Force a Kubernetes API token refresh.
  x           Switch context within the active kubeconfig.
```

### Set configuration file command

```bash
ak c --help

Usage: ak c [OPTIONS] KUBECONFIG_NAME

  Copies the specified kubeconfig to a temporary location, refreshing tokens
  if necessary, and prints an 'export KUBECONFIG=...' statement. This allows
  you to quickly switch between different Kubernetes clusters.

  Example: ak c dev

Options:
  --help  Show this message and exit.
```

### Set current context command

```bash
ak x --help

Usage: ak x [OPTIONS] CONTEXT_NAME

  Select a different context in the existing kubeconfig, then update your
  shell prompt accordingly. Great for switching namespaces or cluster contexts
  without changing the underlying kubeconfig file.

  Example: ak x kube-system

Options:
  --help  Show this message and exit.
```

### Refresh token(s) command 

```bash
ak r --help

Usage: ak r [OPTIONS]

  Refresh Kubernetes tokens in the current (or specified) kubeconfig file,
  ensuring your local environment remains authenticated. Useful if the token
  expires or you just want to proactively refresh.

  Example: ak r --kubeconfig dev

Options:
  -k, --kubeconfig TEXT  Name of kubeconfig file to refresh. Use 'all' to
                         refresh all kubeconfigs.
  --help                 Show this message and exit.
```

### Completion command

```bash
ak completion --help

Usage: ak completion [OPTIONS] [[bash|zsh|fish]]

  Generates an official Click completion script for your chosen shell (bash,
  zsh, or fish) and a custom wrapper that updates environment variables. You
  can source this script for interactive tab-completion.

  Example:   eval "$(ak completion bash)"

Options:
  --help  Show this message and exit.
```

---

## Configuration

**ak** uses a configuration file located at `~/.config/ak/config.ini`.

Example configuration:

```ini
[aws]
credentials_file = /home/user/.aws/credentials
token_validity_seconds = 43200
default_profile = company

[aws.company]
original_profile = company-root
authenticated_profile = company-root-mfa
mfa_serial = arn:aws:iam::3453453454345:mfa/yubikey4

[aws.company-dev-root]
original_profile = company-dev-root
authenticated_profile = company-dev-root-mfa
mfa_serial = arn:aws:iam::345345345343:mfa/yubikey4

[aws.company-prod-root]
original_profile = company-prod-root
authenticated_profile = company-prod-root-mfa
mfa_serial = arn:aws:iam::800175841235:mfa/yubikey4

[aws.home]
original_profile = home-systems
authenticated_profile = home-systems-mfa
mfa_serial = arn:aws:iam::262626262626:mfa/yubikey4

[aws.home-root]
original_profile = home-systems-root
authenticated_profile = home-systems-root-mfa
mfa_serial = arn:aws:iam::239087474744:mfa/yubikey4

[kube]
configs_dir = /home/user/.kubeconfigs
temp_dir = /home/user/.kubeconfigs_temp
token_validity_seconds = 900
```

---

## Testing

### Run Tests with Pytest Directly

```bash
pytest tests/ --verbose
```

### Using Make

```bash
make test
```

### Coverage Reports

Generate coverage reports using:

```bash
make coverage
```

This command runs `pytest --cov` to generate a detailed coverage report.

---

## For further reference

- [ak api documentation](https://aharonh.github.io/ak-tool/)
- [aws cli config documentation](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html)
- [kubeconfig v1 documentation](https://kubernetes.io/docs/reference/config-api/kubeconfig.v1/)

## Final Notes

**ak** is designed to reduce operational overhead by consolidating AWS and Kubernetes authentication tasks. Whether you’re switching contexts, refreshing tokens, or managing multiple environments, **ak** provides a streamlined and efficient workflow.

Happy coding!
