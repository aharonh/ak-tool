Usage Guide
===========

Overview
--------

ak centralizes AWS MFA login, Kubernetes context switching, and token refresh. 
It includes these core commands:

- **l (login)**: ``ak l <mfa_code>``
- **c (switch kubeconfig)**: ``ak c <kube_name>``
- **x (switch context)**: ``ak x <context_name>``
- **r (refresh token)**: ``ak r``
- **completion**: ``ak completion bash|zsh|fish``

Examples
--------

**AWS MFA Login**:

.. code-block:: bash

   ak l 123456

This command retrieves short-lived AWS credentials under your configured
"authenticated_profile" and sets ``AWS_PROFILE`` in your environment.

**Switch Kubeconfig**:

.. code-block:: bash

   ak c dev

Copies the specified kubeconfig to a temporary file, replacing references to
``aws-iam-authenticator`` with short-lived tokens.

**Switch Context**:

.. code-block:: bash

   ak x kube-system

Allows you to select a different context within the same kubeconfig. 
Shell prompt updates accordingly (if you have the prompt script sourced).

**Force Token Refresh**:

.. code-block:: bash

   ak r

Forces a refresh of the Kubernetes API token in the current (or specified) kubeconfig.

**Completion**:

.. code-block:: bash

   ak completion bash

Displays a script that you can source to enable tab completion. 
See :ref:`quickstart` for more details on shell completion.

Multiple Kubeconfigs & Namespaces
---------------------------------
You can maintain multiple kubeconfigs for dev, staging, or production. 
For example:

.. code-block:: bash

   ak c prod
   ak x kube-system

Switching from one environment to another is just a single command away.

Automatic or On-Demand Token Refresh
------------------------------------
When the Kubernetes API token expires but the AWS session token remains valid, ak 
automatically refreshes the token. If you want to proactively refresh, use:

.. code-block:: bash

   ak r
