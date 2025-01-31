import os
import configparser
from pathlib import Path


class AKConfig:
    """
    Loads and manages configuration for AWS + Kube usage, including multiple
    AWS profiles in sections like [aws.company], [aws.home], etc.
    """

    def __init__(self, config_path: str = "~/.config/ak/config.ini"):
        self.config_path = os.path.expanduser(config_path)
        self._cp = configparser.ConfigParser()
        self._ensure_exists()
        self._cp.read(self.config_path)

    def _ensure_exists(self):
        """
        If the config file does not exist, create a default one with minimal sections.
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

            # Kube defaults
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
        Save changes back to the config file.
        """
        with open(self.config_path, "w") as f:
            self._cp.write(f)

    # ----------------------------------------------------------------------
    # GLOBAL AWS PROPERTIES
    # ----------------------------------------------------------------------

    @property
    def credentials_file(self) -> str:
        return self._cp["aws"]["credentials_file"]

    @property
    def aws_global_token_validity_seconds(self) -> int:
        """
        The global default token validity (e.g., 43200s = 12h)
        """
        return int(self._cp["aws"].get("token_validity_seconds", "43200"))

    @property
    def default_aws_profile(self) -> str:
        return self._cp["aws"]["default_profile"]

    # ----------------------------------------------------------------------
    # MULTIPLE AWS PROFILES
    # ----------------------------------------------------------------------

    def get_aws_profile(self, profile_name: str) -> dict:
        """
        Retrieve AWS profile info (original_profile, authenticated_profile,
        mfa_serial, etc.) from [aws.<profile_name>] section. Falls back to global
        defaults for token validity.
        """
        section = f"aws.{profile_name}"
        if section not in self._cp:
            raise KeyError(f"No such profile section: [{section}]")

        data = {}
        data["original_profile"] = self._cp[section].get("original_profile", "")
        data["authenticated_profile"] = self._cp[section].get(
            "authenticated_profile", ""
        )
        data["mfa_serial"] = self._cp[section].get("mfa_serial", "")

        # Optionally, allow overriding token validity in each sub-section
        # If not present, use the global one
        if "token_validity_seconds" in self._cp[section]:
            data["token_validity_seconds"] = int(
                self._cp[section]["token_validity_seconds"]
            )
        else:
            data["token_validity_seconds"] = self.aws_global_token_validity_seconds

        return data

    # ----------------------------------------------------------------------
    # KUBE SECTION
    # ----------------------------------------------------------------------

    @property
    def kube_configs_dir(self) -> str:
        return self._cp["kube"]["configs_dir"]

    @property
    def kube_temp_dir(self) -> str:
        return self._cp["kube"]["temp_dir"]

    @property
    def kube_token_validity_seconds(self) -> int:
        return int(self._cp["kube"]["token_validity_seconds"])

    @property
    def default_kube_config(self) -> str:
        return self._cp["kube"]["default_config"]
