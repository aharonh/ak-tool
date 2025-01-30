# The ak (access kubernetes) tool

This project consolidates AWS MFA login, Kubernetes context switching, and Kubernetes API token refreshing into one simple cli tool (`ak.sh`).

It is especially useful to engineers for working multiple kubernetes clusters running in multiple AWS accounts and configured with OpenID Connect SSO for kubernetes user authentication, further secured with AWS policy requiring MFA. 

## Quick start

1. Install dependencies

   for working in virtual environment

   ```bash
   cd ak
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   for local install
   ```bash
   cd ak
   pip3 install -r requirements.txt
   ```

2. Source the shell script:

   ```bash
   source bin/ak.sh
   ```

3. Run
   ```bash
    # AWS login with MFA code
    ak l 123456

    # Switch to a particular kube config
    ak c dev

    # Switch to a named context
    ak x kube-system
   ```

4. Prompt and Environment variables

    After you run **ak c some-kubeconfig** or **ak x some-context**, the **PS1** environment variable controlling the prompt is updated to contain the current kubernetes context set in *some-kubeconfig* file.
    
    The environment variables for AWS_PROFILE is also updated to reflect the aws profile associated with current context.

5. For persistent setup

    If you open a new shell, you’d have to re-source bin/ak.sh. For frequent use, put that in your ~/.bashrc.

    ```bash
    source /path/to/ak/bin/ak.sh
    ```

## Introduction

The tool is aimed at simplifies the commands required to run in order to authenticate and navigate the clusters. 

## Features

- Streamlined authentication 
- The kubernetes API token caching
- Streamline work with multiple kubeconfigs
- Streamline work with multiple namespaces
- Refresh tokens automatically or on demand
- The kubernetes and aws profile current context synchronization

### Streamlined authentication 

In secure aws kubernetes environments we often have have SSO and mfa enabled with limited token lifespans. This adds some complexity to daily operation and ak tries to streamline this.

For aws cli access to you aws account, you need on each day to generate a new session token and it will be by default valid for 12 hours. Then in turn, to authenticate with kubernetes, you then need to issue a commonly short lived (15 minutes) token. 

The **aws sts** parameter **--duration-seconds** controls the token expiration and aws-iam-authenticator **--expiration** parameter does the same for kubernetes api access token. 

With ak, you think once about parameters, configure them in the configuration file, and aws session token is retrieved as follows:

```bash
me@laptop ~/src/ak $ ak l 123456
```

The kubernetes API token is automatically managed as usually.

### The kubernetes API token caching

For kops based clusters, **ak** adds the missing feature of caching the kubernetes authentication token. Without the token caching, each kubectl command creates new token and therefore, slows-down the work significantly. 

The eks clusters users already have the kubernetes token caching feature, yet perhaps may still benefit from this tool from the configuration flexibility as well as in its other features.

### Streamline work with multiple kubeconfigs 

Switching among multiple kubeconfigs (dev, test, prod, etc.).


### Streamline work with multiple namespaces

You will typically create a context in kubeconfig file per kubernetes namespace in relevant cluster/clusters. 
Switching multiple namespaces contexts 

```bash
kubectl config set-context kube-system
```

```bash
ak c kube-system
```

The current context is always in your shell prompt

```bash
(.venv) me@laptop ~/src/ak {dev-kube-system} $ 
```

### Refresh tokens automatically or on demand

When a kubernetes api token is expired and the aws token is stil valid, the tool automatically renews the token.


### The kubernetes and aws profile current context synchronization

Each context in kubeconfig may be associated to different aws account. When switching the context, the AWS_PROFILE environment variable is adjusted so that your subsequent aws commands will run in that context.

## Testing

We use pytest. In a virtualenv or environment with dependencies:

```bash
pytest tests/ --verbose
```

or just
```bash
make test
```

To generate coverage report, run:

```bash
pytest --cov=src/ak --cov-report=xml
```

or just:
```bash
make coverage
```