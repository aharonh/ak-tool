from src.ak_cli.config import AKConfig
from src.ak_cli.core import AWSManager, KubeManager
from src.ak_cli.logger import setup_logger


def test_aws_manager_init():
    cfg = AKConfig()
    logger = setup_logger(debug=True)
    aws = AWSManager(cfg, logger, "home")
    assert aws.config is cfg


def test_kube_manager_init():
    cfg = AKConfig()
    logger = setup_logger(debug=True)
    kube = KubeManager(cfg, logger)
    assert kube.config is cfg
