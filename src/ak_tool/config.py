import os
import configparser
from pathlib import Path


class AKConfig:
    """
    Loads and manages configuration for AWS and Kubernetes usage, including multiple
    AWS profiles in sections like ``[aws.company]``, ``[aws.home]``, etc.
    """

    def __init__(self, config_path: str = "~/.config/ak/config.ini"):
        """
        Initialize the AKConfig object.

        This method expands the user path, ensures the configuration file exists,
        and loads the configuration.

        :param config_path: Path to the configuration file.
                            Defaults to "~/.config/ak/config.ini".
        :type config_path: str
        """
        self.config_path = os.path.expanduser(config_path)
        self._cp = configparser.ConfigParser()
        self._ensure_exists()
        self._cp.read(self.config_path)

    def _ensure_exists(self):
        """
        Ensure that the configuration file exists.

        If the configuration file does not exist, create a default one with minimal
        sections for AWS and Kubernetes.
        """
        if not os.path.exists(self.config_path):
            config_dir = os.path.dirname(self.config_path)
            Path(config_dir).mkdir(parents=True, exist_ok=True)

            # Global AWS defaults
            self._cp["aws"] = {
                "credentials_file": os.path.expanduser("~/.aws/credentials"),
                "token_validity_seconds": "43200",  # 12 hours by default
                "default_profile": "home",
            }

            # Example for a 'home' sub-profile
            self._cp["aws.home"] = {
                "original_profile": "home",
                "authenticated_profile": "home-authenticated",
                "mfa_serial": "arn:aws:iam::222222222:mfa/token",
            }

            # Kubernetes defaults
            self._cp["kube"] = {
                "configs_dir": os.path.expanduser("~/.kubeconfigs"),
                "temp_dir": os.path.expanduser("~/.kubeconfigs_temp"),
                "token_validity_seconds": "900",
                "default_config": "home",
            }

            with open(self.config_path, "w") as f:
                self._cp.write(f)

    def save(self):
        """
        Save any changes made to the configuration back to the configuration file.
        """
        with open(self.config_path, "w") as f:
            self._cp.write(f)

    # ----------------------------------------------------------------------
    # GLOBAL AWS PROPERTIES
    # ----------------------------------------------------------------------

    @property
    def credentials_file(self) -> str:
        """
        Get the path to the AWS credentials file.

        :return: AWS credentials file path.
        :rtype: str
        """
        return self._cp["aws"]["credentials_file"]

    @property
    def aws_global_token_validity_seconds(self) -> int:
        """
        Get the global default token validity in seconds.

        This is the default duration for which an AWS token remains valid (e.g., 43200s = 12 hours).

        :return: Token validity duration in seconds.
        :rtype: int
        """
        return int(self._cp["aws"].get("token_validity_seconds", "43200"))

    @property
    def default_aws_profile(self) -> str:
        """
        Get the default AWS profile name.

        :return: Default AWS profile.
        :rtype: str
        """
        return self._cp["aws"]["default_profile"]

    # ----------------------------------------------------------------------
    # MULTIPLE AWS PROFILES
    # ----------------------------------------------------------------------

    def get_aws_profile(self, profile_name: str) -> dict:
        """
        Retrieve AWS profile information for a given profile.

        This method fetches details such as ``original_profile``, ``authenticated_profile``,
        and ``mfa_serial`` from the configuration section ``[aws.<profile_name>]``.
        It also retrieves a token validity value, which may override the global default.

        :param profile_name: The name of the AWS profile (without the "aws." prefix).
        :type profile_name: str
        :raises KeyError: If the profile section ``[aws.<profile_name>]`` does not exist.
        :return: A dictionary containing the AWS profile information.
        :rtype: dict
        """
        section = f"aws.{profile_name}"
        if section not in self._cp:
            raise KeyError(f"No such profile section: [{section}]")

        data = {
            "original_profile": self._cp[section].get("original_profile", ""),
            "authenticated_profile": self._cp[section].get("authenticated_profile", ""),
            "mfa_serial": self._cp[section].get("mfa_serial", ""),
        }

        # Optionally allow overriding token validity for the specific profile.
        if "token_validity_seconds" in self._cp[section]:
            data["token_validity_seconds"] = int(
                self._cp[section]["token_validity_seconds"]
            )
        else:
            data["token_validity_seconds"] = self.aws_global_token_validity_seconds

        return data

    # ----------------------------------------------------------------------
    # KUBERNETES CONFIGURATION
    # ----------------------------------------------------------------------

    @property
    def kube_configs_dir(self) -> str:
        """
        Get the directory where Kubernetes configuration files are stored.

        :return: Kubernetes configuration directory path.
        :rtype: str
        """
        return self._cp["kube"]["configs_dir"]

    @property
    def kube_temp_dir(self) -> str:
        """
        Get the temporary directory used for storing Kubernetes tokens.

        :return: Temporary Kubernetes directory path.
        :rtype: str
        """
        return self._cp["kube"]["temp_dir"]

    @property
    def kube_token_validity_seconds(self) -> int:
        """
        Get the Kubernetes API token validity duration in seconds.

        :return: Token validity duration in seconds.
        :rtype: int
        """
        return int(self._cp["kube"]["token_validity_seconds"])

    @property
    def default_kube_config(self) -> str:
        """
        Get the default Kubernetes configuration name.

        :return: Default Kubernetes configuration.
        :rtype: str
        """
        return self._cp["kube"]["default_config"]
