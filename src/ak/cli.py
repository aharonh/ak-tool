import sys
from .config import AKConfig
from .logger import setup_logger
from .core import AWSManager, KubeManager


def main():

    debug = False
    if "--debug" in sys.argv:
        debug = True
        sys.argv.remove("--debug")
    logger = setup_logger("ak", debug=debug)

    config = AKConfig()
    aws_mgr = AWSManager(config, logger)
    kube_mgr = KubeManager(config, logger)

    if len(sys.argv) < 2:
        usage()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "l":  # login
            if len(args) < 1:
                print("Usage: ak l <mfa_code>")
                return
            mfa_code = args[0]
            export_line = aws_mgr.mfa_login(mfa_code)
            print(export_line)

        elif cmd == "c":  # config
            if len(args) < 1:
                print("Usage: ak c <kube_name>")
                return
            kube_name = args[0]
            export_line = kube_mgr.switch_config(kube_name)
            print(export_line)

        elif cmd == "x":  # context
            if len(args) < 1:
                print("Usage: ak x <context_name>")
                return
            context_name = args[0]
            export_line = kube_mgr.switch_context(context_name)
            print(export_line)

        elif cmd == "r":  # refresh
            kube_mgr.force_refresh()

        elif cmd == "h":
            usage()

        else:
            print(f"Unknown subcommand: {cmd}")
            usage()
    except Exception as e:
        logger.error(str(e))


def usage():
    print("Usage: ak <subcommand> [args]")
    print("Subcommands:")
    print(" l <mfa_code> : AWS MFA login (MFA)")
    print(" c <kube_name> : Switch kubeconfig")
    print(" x <context> : Switch context within the current KUBECONFIG")
    print(" r : Force token refresh")
    print(" h : Show usage")


if __name__ == "__main__":
    main()
