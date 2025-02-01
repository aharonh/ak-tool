from src.ak_tool.config import AKConfig
from src.ak_tool.core import AWSManager, KubeManager
from src.ak_tool.logger import setup_logger


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
