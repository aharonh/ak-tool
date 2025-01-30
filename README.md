# The **ak** (Access Kubernetes) Tool

This project consolidates AWS MFA login, Kubernetes context switching, and Kubernetes API token refreshing into a single CLI tool (`ak.sh`).

It is useful for engineers who work with multiple Kubernetes clusters in multiple AWS accounts, each configured with OpenID Connect SSO or other secure authentication methods (including MFA).

---

## Quick Start

1. **Install Dependencies**

   **Using a virtual environment:**
   ```bash
   cd ak
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   **Local installation (system-wide or user-wide):**
   ```bash
   cd ak
   pip3 install -r requirements.txt
   ```

2. **Source the Shell Script**

   ```bash
   source bin/ak.sh
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

5. **Persistent Setup**

   - Every new shell session requires re-sourcing `bin/ak.sh`.  
   - For convenience, add this line to `~/.bashrc`:
     ```bash
     source /path/to/ak/bin/ak.sh
     ```

---

## Introduction

`ak` reduces the commands and complexity involved in authenticating to multiple AWS accounts and navigating multiple Kubernetes clusters. It handles AWS MFA tokens, short-lived Kubernetes API tokens, and automatically refreshes them when needed.

---

## Features

- **Streamlined Authentication**  
  - Handles MFA-based logins for AWS and short-lived Kubernetes tokens.  
  - Reduces the steps needed for daily re-authentication.

- **Kubernetes API Token Caching**  
  - Prevents repetitive token generation for kOps-based clusters.  
  - EKS users can still benefit from centralized config management.

- **Multiple Kubeconfig Management**  
  - Easily switch among dev, test, and production clusters.

- **Multiple Namespace Context Switching**  
  - Quickly change between different namespace contexts.  
  - Keeps your current context visible in the shell prompt.

- **Automatic or On-Demand Token Refresh**  
  - Renews Kubernetes API tokens when they expire, as long as the AWS session token remains valid.

- **Kubernetes & AWS Profile Synchronization**  
  - Each kubeconfig context is tied to the appropriate AWS account.  
  - Switching contexts updates `AWS_PROFILE`, so your AWS CLI usage remains consistent with the current cluster.

---

### Streamlined Authentication

In secure AWS/Kubernetes environments, you often have SSO and MFA enabled, with limited token lifespans. By default, an AWS STS session token may only last 12 hours, and a Kubernetes API token might only last 15 minutes. The **ak** tool abstracts away the details by storing MFA and configuration parameters in a single file. Daily re-authentication becomes as simple as:

```bash
ak l 123456
```

---

### Kubernetes API Token Caching

- **Kops-based clusters** often lack built-in token caching, causing every `kubectl` command to generate a new token. This can slow down workflows significantly.  
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
