import os
import argparse

from . import flask_app, release
from . import deploy


def main():
    parser = argparse.ArgumentParser(description=f"cli for hakitool")

    parser.add_argument("--version", "-v", help=f"display version and exit", action="store_true")

    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="run the application")
    if deploy.REQUIREMENTS_INSTALLED:
        deploy_parser = subparsers.add_parser("deploy", help="deploy the application", add_help=False)
        deploy.DeploymentManager.add_deployment_args(deploy_parser)

    args = parser.parse_args()

    # IPS()
    if args.version:
        print(release.__version__)
        return
    elif args.command == "run":
        flask_app.main()
        return
    elif args.command == "deploy":
        deploy.main(args=args)
        return

    parser.print_help()
