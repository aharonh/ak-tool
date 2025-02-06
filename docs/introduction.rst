Introduction
============

ak is a unified CLI tool that simplifies AWS MFA logins, Kubernetes context switching,
and Kubernetes API token refreshing. Designed for engineers managing multiple
Kubernetes clusters across different AWS accounts, **ak** streamlines daily 
authentication and environment management—especially when using OpenID Connect SSO, 
MFA, or other secure authentication methods.

Key Features
------------

- **Streamlined AWS MFA Authentication**:
  - Single command: ``ak l <mfa_code>`` to generate short-lived AWS credentials.
  - Automatic writing of credentials to your AWS profiles.

- **Kubernetes Context Switching**:
  - Swap between multiple kubeconfig files: ``ak c <kube_name>``
  - Change contexts within an active kubeconfig: ``ak x <context_name>``

- **Token Refresh**:
  - Auto or manual refresh for AWS/Kubernetes tokens.
  - ``ak r`` triggers an immediate refresh.

- **Shell Integration**:
  - Colorful dynamic prompts.
  - Environment variables (``AWS_PROFILE``, ``KUBECONFIG``) updated automatically.
  - Completion scripts for bash, zsh, and fish: ``ak completion <shell>``.

Why Use ak?
-----------

Managing multiple AWS accounts and Kubernetes clusters can be complex. 
ak minimizes that complexity by:

- Handling AWS MFA tokens and short-lived Kubernetes API tokens.
- Automating token refreshes.
- Providing a single interface for switching contexts across environments.
- Keeping your current AWS session context and kubecontext in sync.

For a quick start, see :ref:`quickstart`.
