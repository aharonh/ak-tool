Configuration
=============

Overview
--------

The ``ak`` tool requires a configuration file at:

``~/.config/ak/config.ini``

If this file does **not** exist, ``ak`` automatically creates a minimal default
configuration upon first run (see :ref:`minimal-default-config` below). The config
file defines how ``ak``:

- Retrieves and manages **AWS** credentials (including MFA).
- Handles **Kubernetes** kubeconfigs and tokens.

This document describes each configuration section and the relevant keys you can set.

.. contents::
   :local:
   :depth: 2


Global Structure
----------------

A typical ``ak`` configuration file has at least two main sections:

1. A global **[aws]** section for AWS-wide settings (e.g., default credentials file,
   token duration, default profile).
2. One or more **[aws.<profile>]** sections describing specific AWS sub-profiles
   (e.g., `[aws.company]`, `[aws.home]`, `[aws.company-dev-root]`, etc.).
3. A global **[kube]** section for Kubernetes defaults (e.g., where your kubeconfig
   files live, how long tokens last, etc.).

For example:

.. code-block:: ini

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

   [kube]
   configs_dir = /home/user/.kubeconfigs
   temp_dir = /home/user/.kubeconfigs_temp
   token_validity_seconds = 900
   default_config = dev

You can add more or fewer sections to suit your environment.


[aws] Section
-------------

This **global** section controls overall AWS-related defaults. It must be named exactly
``[aws]``. Keys include:

- **credentials_file** (string):
  
  Path to your AWS credentials file. Typically this is
  ``~/.aws/credentials`` but you can set it to any file. When you run
  ``ak l <mfa_code>``, ``ak`` updates credentials in this file.

- **token_validity_seconds** (integer, default = 43200):

  How long temporary AWS credentials remain valid, in **seconds**. By default,
  43200 seconds = 12 hours. If you do not specify a duration in a sub-profile,
  this global value is used.

- **default_profile** (string):

  Name of the AWS sub-profile to use if the user does not explicitly specify
  ``--aws-profile``. For example, if you set `default_profile = home`, then
  running commands without ``--aws-profile`` will fall back to the sub-profile
  `[aws.home]`.

Example:

.. code-block:: ini

   [aws]
   credentials_file = /home/user/.aws/credentials
   token_validity_seconds = 43200
   default_profile = company


[aws.<profile>] Sub-Profiles
----------------------------

Each sub-profile is an additional section named `[aws.<PROFILE_NAME>]`. These define how
``ak`` handles MFA, short-lived AWS credentials, and override token durations (if desired).

Within each sub-profile section, you may configure:

- **original_profile** (string):

  The name of your base AWS CLI profile used to **authenticate** via MFA.
  This profile **must** exist in your AWS credentials file. For example, if
  you have:

  ```
  [company-root]
  aws_access_key_id = ...
  aws_secret_access_key = ...
  ```

  then `original_profile` would be `company-root`.

- **authenticated_profile** (string):

  The name of the AWS CLI profile where **short-lived** credentials (STS tokens)
  are written after MFA login. Typically something like `company-root-mfa`.
  `ak` will automatically write updated credentials under this profile in your
  credentials file.

- **mfa_serial** (string):

  The ARN of the MFA device associated with your AWS account. For example:
  ``arn:aws:iam::123456789012:mfa/your.username``

- **token_validity_seconds** (integer, optional):

  If present, overrides the global `[aws].token_validity_seconds` for this sub-profile only.
  This allows certain profiles to have shorter or longer MFA validity periods. If omitted,
  the global default is used.

Example:

.. code-block:: ini

   [aws.company]
   original_profile = company-root
   authenticated_profile = company-root-mfa
   mfa_serial = arn:aws:iam::3453453454345:mfa/yubikey4

   [aws.home]
   original_profile = home-systems
   authenticated_profile = home-systems-mfa
   mfa_serial = arn:aws:iam::262626262626:mfa/yubikey4

   [aws.company-dev-root]
   original_profile = company-dev-root
   authenticated_profile = company-dev-root-mfa
   mfa_serial = arn:aws:iam::111111111111:mfa/dev-yubikey4
   token_validity_seconds = 7200  ; 2 hours just for dev

When you run:

.. code-block:: bash

   ak l 123456 --aws-profile company

``ak``:

1. Looks up `[aws.company]`
2. Uses `company-root` as `original_profile`
3. Writes short-lived credentials to `company-root-mfa`
4. Applies the sub-profile’s `mfa_serial`
5. Uses either the sub-profile’s `token_validity_seconds`, or if not set, the global `[aws]` value.


[kube] Section
--------------

This section handles Kubernetes-specific settings. It **must** be named `[kube]`.
Keys include:

- **configs_dir** (string, default = ``~/.kubeconfigs``):

  Directory where you store your named kubeconfig files (e.g., `dev`, `prod`, `staging.yaml`, etc.).
  You switch among these with ``ak c <kube_name>``.

- **temp_dir** (string, default = ``~/.kubeconfigs_temp``):

  Directory where ``ak`` writes out **temporary** kubeconfig files, containing
  short-lived tokens. This prevents you from overwriting your original kubeconfigs.

- **token_validity_seconds** (integer, default = 900):

  Kubernetes token validity in seconds. By default, 900 seconds = 15 minutes.
  Once the token expires, ``ak`` will automatically re-generate a new token
  upon the next command (or you can run ``ak r`` to force a refresh).

- **default_config** (string, optional):

  The default kubeconfig name if you do not specify one in commands like
  ``ak c`` or in your environment variables. If omitted, you must always
  provide an explicit kubeconfig name.

Example:

.. code-block:: ini

   [kube]
   configs_dir = /home/user/.kubeconfigs
   temp_dir = /home/user/.kubeconfigs_temp
   token_validity_seconds = 900
   default_config = dev

In this example:
- ``ak c dev`` copies `/home/user/.kubeconfigs/dev` to a file in `/home/user/.kubeconfigs_temp`.
- The new file has AWS-based entries replaced with static tokens that remain valid for 15 minutes.
- If you omit `dev`, it defaults to whatever is under `default_config`.


Minimal Default Config
----------------------
.. _minimal-default-config:

If ``~/.config/ak/config.ini`` is **missing**, ``ak`` automatically creates a minimal
config file with the following sections:

.. code-block:: ini

   [aws]
   credentials_file = /home/<USER>/.aws/credentials
   token_validity_seconds = 43200
   default_profile = home

   [aws.home]
   original_profile = home
   authenticated_profile = home-authenticated
   mfa_serial = arn:aws:iam::222222222:mfa/token

   [kube]
   configs_dir = /home/<USER>/.kubeconfigs
   temp_dir = /home/<USER>/.kubeconfigs_temp
   token_validity_seconds = 900
   default_config = home

Adjust these defaults to fit your environment.


Tips & Best Practices
---------------------

1. **Keep AWS Credentials Secure**  
   Your `credentials_file` path should be readable only by your user. 
   Avoid committing it to version control.

2. **Use Distinct Sub-Profiles**  
   For each AWS environment (dev, prod, personal, etc.), create a separate 
   `[aws.<profile>]` so you can run ``ak l`` with the correct `--aws-profile`.

3. **Shorter Durations in Sensitive Environments**  
   If you want more frequent re-authentication, reduce `token_validity_seconds` in 
   a sub-profile. E.g., `[aws.company-prod-root] token_validity_seconds=3600`.

4. **Automate**  
   Place commands like `eval "$(ak completion bash)"` in your `.bashrc` or `.zshrc`.
   You can also define an alias if you find yourself switching contexts frequently.

5. **Check Context**  
   After switching kubeconfigs, you can run `kubectl config current-context` 
   (or `ak x <context>`) to confirm you’re in the correct environment.


Conclusion
----------

By customizing `[aws]`, `[aws.<profile>]`, and `[kube]` sections, you can tailor
ak to your specific AWS+Kubernetes environments. For further usage instructions,
see :ref:`usage`.

For an in-depth look at the internal config loading logic, refer to the 
:doc:`API Reference <api>` (specifically the `ak_tool.config` module).

