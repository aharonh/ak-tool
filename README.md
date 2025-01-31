# The **ak** (access kubernetes) tool

This project consolidates AWS MFA login, Kubernetes context switching, and Kubernetes API token refreshing into a single CLI tool (`ak`). It is useful for engineers who work with multiple Kubernetes clusters in multiple AWS accounts, each configured with OpenID Connect SSO or other secure authentication methods (including MFA).

---

Table of Contents
- [The **ak** (access kubernetes) tool](#the-ak-access-kubernetes-tool)
  - [Quick Start](#quick-start)
  - [Introduction](#introduction)
  - [Features](#features)
    - [Streamlined AWS MFA Authentication](#streamlined-aws-mfa-authentication)
      - [**How It Works**](#how-it-works)
      - [**Configuration Breakdown**](#configuration-breakdown)
      - [**AWS CLI Configuration**](#aws-cli-configuration)
      - [**How `ak` Updates Credentials**](#how-ak-updates-credentials)
    - [Streamlined Kubernetes API Authentication](#streamlined-kubernetes-api-authentication)
    - [Multiple Kubeconfigs \& Namespaces](#multiple-kubeconfigs--namespaces)
    - [Automatic or On-Demand Token Refresh](#automatic-or-on-demand-token-refresh)
    - [Kubernetes \& AWS Profile Synchronization](#kubernetes--aws-profile-synchronization)
    - [Completion](#completion)
  - [Command line parameters](#command-line-parameters)
  - [Configuration](#configuration)
  - [Testing](#testing)

## Quick Start

1. **Install Dependencies**

   **Using a virtual environment:**
   ```bash
   cd ak
   python3 -m venv .venv
   source .venv/bin/activate
   make install
   ```

   **Local installation:**
   ```bash
   cd ak
   make install
   ```

2. **Source the completion script**

   ```bash
   eval "$(ak completion bash)"
   ```

3. **Run `ak` Commands**
   ```bash
   # AWS login with MFA code:
   ak l 123456

   # Switch to a particular kubeconfig:
   ak c dev

   # Switch to a named context:
   ak x kube-system
   ```

4. **Prompt & Environment Variables**

   - After running `ak c <kubeconfig>` or `ak x <context>`, the shell prompt (`PS1`) is updated to reflect the active context.
   - The `AWS_PROFILE` environment variable is also updated to match the AWS account linked to the new context.


---

## Introduction

`ak` reduces the commands and complexity involved in authenticating to multiple AWS accounts and navigating multiple Kubernetes clusters. It handles AWS MFA tokens, short-lived Kubernetes API tokens, and automatically refreshes them when needed.

---

## Features

- **Streamlined AWS MFA Authentication**
  - Handles MFA-based logins for AWS and short-lived Kubernetes tokens.  
  - Reduces the steps needed for daily re-authentication.

- **Streamlined Kubernetes API Authentication**  
  - Prevents repetitive token generation for kOps-based clusters.  
  - EKS users can still benefit from centralized config management.

- **Multiple Kubeconfig Management**  
  - Easily switch among dev, test, and production clusters.

- **Multiple Namespace Context Switching**  
  - Quickly change between different namespace contexts.  
  - Automatically refreshes Kubernetes tokens when needed.

- **Automatic or On-Demand Token Refresh**  
  - Renews Kubernetes API tokens when they expire, as long as the AWS session token remains valid.

- **Kubernetes & AWS Profile Synchronization**  
  - Each kubeconfig context is tied to the appropriate AWS account.  
  - Switching contexts updates `AWS_PROFILE`, so your AWS CLI usage remains consistent with the current cluster.

- **User friendly**
  - The commands are short, documented and they autocomplete
  - Updated prompt with current git branch, kubeconfig and kubernetes context



---

### Streamlined AWS MFA Authentication

In secure AWS/Kubernetes environments, **SSO and MFA** are commonly required, often with short-lived credentials. An AWS **STS session token** typically expires in **12 hours**, while a **Kubernetes API token** may last only **15 minutes**. The **ak** tool simplifies re-authentication by managing AWS MFA and Kubernetes configuration in a **single** place.

With **ak**, daily authentication is reduced to a **single command**:

```bash
ak l 123456
```

#### **How It Works**
The authentication process follows a **dual-profile model**:

- **Original Profile** → Used for MFA authentication with AWS.
- **Authenticated Profile** → Stores the temporary credentials post-MFA.

This allows **ak** to fetch a fresh session token and store it under the **authenticated profile**. You can configure **multiple AWS accounts**, each with its own authentication setup. Below is an example of the **ak** configuration file:

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

#### **Configuration Breakdown**
- **credentials_file** → Path to the AWS credentials file.
- **token_validity_seconds** → Duration (in seconds) for which the temporary credentials remain valid.
- **default_profile** → The default AWS profile used when `--aws-profile` is not specified.
- **aws.<profile_name>** → Defines different authentication setups per AWS account.
- **original_profile** → AWS profile used for initial MFA authentication.
- **authenticated_profile** → AWS profile where temporary credentials are stored.
- **mfa_serial** → ARN of the MFA device used for authentication.

#### **AWS CLI Configuration**
For **ak** to work correctly, your AWS **config** and **credentials** files must be properly set up. Below is an example AWS **config file**:

```ini
[profile company-root]
region = us-east-1
output = json

[profile company-root-mfa]
region = us-east-1
output = json
```

And a corresponding **AWS credentials file**:

```ini
[company-root]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[company-root-mfa]
aws_access_key_id = ASIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws_session_token = FQoGZXIvYXdzEJr//////////wEaDIN
```

#### **How `ak` Updates Credentials**
When you run:

```bash
ak l 123456
```

The **ak** tool:
1. Uses the **original profile** to authenticate with AWS and perform **MFA validation**.
2. Retrieves a temporary **STS session token**.
3. Writes the new credentials under the **authenticated profile** in `~/.aws/credentials`.
4. Automatically switches AWS authentication to the **authenticated profile**.

The `[company-root-mfa]` section in the credentials file is dynamically updated by **ak**, ensuring you always have valid credentials.

---

### Streamlined Kubernetes API Authentication

- **Kops-based clusters** often lack built-in token caching, causing every `kubectl` command to generate a new token. This can **slow down workflows significantly**.  
- **ak** caches these tokens to improve performance.  
- **EKS-based clusters** generally have some caching by default, but can still benefit from ak for multi-cluster config management.

---

### Multiple Kubeconfigs & Namespaces

- Switch quickly among dev, test, and prod configs:
  ```bash
  ak c prod
  ```
- Switch among multiple namespace contexts within a single cluster:
  ```bash
  ak x kube-system
  ```
- The active context is shown in your shell prompt, e.g. `(dev-kube-system) $ `.

---

### Automatic or On-Demand Token Refresh

- When the Kubernetes API token expires but the AWS session token is still valid, **ak** automatically regenerates the Kubernetes token.  
- You can also force a refresh manually with:
  ```bash
  ak r
  ```

---

### Kubernetes & AWS Profile Synchronization

- For each kubeconfig context that specifies AWS profile in the user's command, when you run `ak x <context>`, **ak** exports `AWS_PROFILE` so your other AWS CLI commands use the matching account.  

### Completion

 - ak supports tab-completion for bash, zsh and fish shell. to enable it run:

   ```bash
   eval "$(ak completion bash)"
   ```

   to have the completion always enables fpr bash:

   ```bash
   ak completion bash | sudo tee /etc/etc/bash_completion.d/ak
   . /etc/etc/bash_completion.d/ak
   ```

## Command line parameters

Below is the documentation for the commands that **ak** supports:

```bash
ak --help
Usage: ak [OPTIONS] COMMAND [ARGS]...

Options:
  --debug             Enable debug logging.
  --aws-profile TEXT  Name of AWS sub-profile section, e.g. 'company', 'home'.
  --help              Show this message and exit.

Commands:
  c           Switch to a specific kubeconfig by name.
  completion  Generate a shell completion script and custom function...
  l           AWS MFA login.
  r           Force token refresh for the current KUBECONFIG.
  x           Switch context within the current KUBECONFIG.
```

---

## Configuration

The configuration file location is `~/.config/ak/config.ini`.

Below is sample configuration file for **ak**:

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

1. **Run Pytest Directly**  
   ```bash
   pytest tests/ --verbose
   ```

2. **Using Make**  
   ```bash
   make test
   ```

3. **Coverage**  
   ```bash
   make coverage
   ```
   Generates coverage reports with `pytest --cov`.

---
