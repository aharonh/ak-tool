Commands
========

ak l
-----
**Usage**:

.. code-block:: bash

   ak l [MFA_CODE]

Performs an AWS MFA login, generating short-lived credentials.

**Options**:

- **MFA_CODE** (string): 6 or 8-digit MFA code from your authenticator.

ak c
-----
**Usage**:

.. code-block:: bash

   ak c [KUBE_NAME]

Copies the specified kubeconfig, injecting short-lived tokens if needed.

**Options**:

- **KUBE_NAME** (string): The kubeconfig name in your ``configs_dir``.

ak x
-----
**Usage**:

.. code-block:: bash

   ak x [CONTEXT_NAME]

Switch contexts within the same kubeconfig.

**Options**:

- **CONTEXT_NAME** (string): The Kubernetes context name.

ak r
-----
**Usage**:

.. code-block:: bash

   ak r [OPTIONS]

Forces a refresh of the Kubernetes API tokens.

**Options**:

- **--kubeconfig, -k** (string): Name of kubeconfig to refresh. Use ``all`` to refresh all kubeconfigs.

ak completion
-------------
**Usage**:

.. code-block:: bash

   ak completion [bash|zsh|fish]

Generates a shell completion script for bash, zsh, or fish.
