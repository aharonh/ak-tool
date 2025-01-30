import os
import configparser
from pathlib import Path


class AKConfig:
    """Loads and manages configuration for AWS + Kube usage."""

    def __init__(self, config_path: str = "~/.config/ak/config.ini"):
        self.config_path = os.path.expanduser(config_path)
        self._cp = configparser.ConfigParser()
        self._ensure_exists()
        self._cp.read(self.config_path)

    def _ensure_exists(self):
        """
        If config file does not exist, create a default one.
        """
        if not os.path.exists(self.config_path):
            config_dir = os.path.dirname(self.config_path)
            Path(config_dir).mkdir(parents=True, exist_ok=True)
            self._cp["aws"] = {
                "original_profile": "root",
                "authenticated_profile": "root-mfa",
                "credentials_file": os.path.expanduser("~/.aws/credentials"),
                "mfa_serial": "arn:aws:iam::222222222:mfa/name.lastname",
                "token_validity_seconds": "43200"
            }
            self._cp["kube"] = {
                "configs_dir": os.path.expanduser("~/.kubeconfigs"),
                "temp_dir": os.path.expanduser("~/.kubeconfigs_temp"),
                "token_validity_seconds": "900",
            }
            with open(self.config_path, "w") as f:
                self._cp.write(f)

    def save(self):
        """
        Save changes back to the config file.
        """
        with open(self.config_path, "w") as f:
            self._cp.write(f)

    @property
    def original_profile(self) -> str:
        return self._cp["aws"]["original_profile"]

    @property
    def authenticated_profile(self) -> str:
        return self._cp["aws"]["authenticated_profile"]

    @property
    def credentials_file(self) -> str:
        return self._cp["aws"]["credentials_file"]

    @property
    def mfa_serial(self) -> str:
        return self._cp["aws"]["mfa_serial"]

    @property
    def aws_token_validity_seconds(self) -> str:
        return self._cp["aws"]["token_validity_seconds"]

    @property
    def kube_configs_dir(self) -> str:
        return self._cp["kube"]["configs_dir"]

    @property
    def kube_temp_dir(self) -> str:
        return self._cp["kube"]["temp_dir"]

    @property
    def kube_token_validity_seconds(self) -> int:
        return int(self._cp["kube"]["token_validity_seconds"])
