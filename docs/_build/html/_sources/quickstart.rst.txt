Quick Start
===========

Installation
------------

Install via PyPI:

.. code-block:: bash

   pip install ak-tool

Or from source:

.. code-block:: bash

   git clone https://github.com/aharonh/ak-tool.git
   cd ak-tool
   python3 -m venv .venv
   source .venv/bin/activate
   make install

Generating Shell Completion
---------------------------

Bash example:

.. code-block:: bash

   eval "$(ak completion bash)"

Zsh:

.. code-block:: bash

   eval "$(ak completion zsh)"

Fish:

.. code-block:: bash

   ak completion fish | source

Basic Usage
-----------

- **AWS Login with MFA Code**:

  .. code-block:: bash

     ak l 123456

- **Switch to a Particular Kubeconfig**:

  .. code-block:: bash

     ak c dev

- **Switch to a Named Context**:

  .. code-block:: bash

     ak x kube-system

Prompt & Environment Variables
------------------------------

After running ``ak c <kubeconfig>`` or ``ak x <context>``, your shell prompt (PS1) reflects
the active context. The ``AWS_PROFILE`` environment variable automatically matches the AWS
account linked to the new context. The ``KUBECONFIG`` environment variable updates to
point to the correct kubeconfig file.
