Usage Guide
===========

This document provides a quick overview on how to install and use the ``ak`` CLI tool.

Installation
------------

To install the tool, run:

.. code-block:: bash

   pip install ak

Using the CLI
-------------

After installation, you can invoke the tool on the command line. For example, to see the help message, run:

.. code-block:: bash

   ak --help

The primary commands include:

- **AWS MFA Login:**  
  Use ``ak l <mfa_code>`` to perform an MFA login and retrieve temporary AWS credentials.

- **Switch Kubeconfig:**  
  Use ``ak c <kube_name>`` to switch to a specific Kubernetes configuration.

- **Switch Context:**  
  Use ``ak x <context_name>`` to change the Kubernetes context within the current kubeconfig.

- **Force Refresh:**  
  Use ``ak r`` to force a refresh of your Kubernetes API token.

- **Shell Completion:**  
  Generate shell completion scripts with ``ak completion <shell>`` where ``<shell>`` can be ``bash``, ``zsh``, ``fish``, or ``powershell``.

Configuration
-------------

The tool loads its configuration from the file located at:

.. code-block:: bash

   ~/.config/ak/config.ini

Ensure that your configuration file is set up correctly for your AWS and Kubernetes environments.