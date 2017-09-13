import argparse
import sys
import os
import json
import pkg_resources  # part of setuptools
from . import terraform_remote_state

class CLIDriver(object):

    MODULE_CONFIG = ".tfrconf"

    def __init__(self):

        self.args = self.accept_cli_args()

        version = pkg_resources.require("tfr")[0].version

        if self.args['version']:
            print(version)
            sys.exit(0)
        self.args['version'] = version

        self.validate_args()

        self.init_env()
        terraform_remote_state.TRS(self.args)

    def accept_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--path", help="module path", default=".", type=str)
        parser.add_argument("-r", "--region", help="AWS Region", default="us-east-1", type=str)
        parser.add_argument("-b", "--bucket", help="S3 Bucket", type=str)
        parser.add_argument("-a", "--app", help="Application Name", type=str)
        parser.add_argument("-e", "--env", help="Environment (ie. dev, test, qa, prod)", type=str)
        parser.add_argument("-ap", "--awsprofile", help="AWS Config Profile", default="default", type=str)
        parser.add_argument("--auto_version", help="Auto-Increment Terraform Version", action='store_true')
        parser.add_argument("-f", "--force", help="Force a TFR conf file update", action='store_true')
        parser.add_argument("-v", "--version", help="Version of toi", action='store_true')

        return vars(parser.parse_args())

    def validate_args(self):
        if not self.args['bucket'] and not self.args['app'] and not self.args['env']:
            if os.path.exists(self.MODULE_CONFIG):
                config = open(self.MODULE_CONFIG, "r").read()
                self.args = json.loads(config)
            else:
                parser.error("Must specify --bucket, --app, and --env")
        elif os.path.exists(self.MODULE_CONFIG):
            if not self.args['force']:
                uinput = input("You are about to override .tfrconf, continue? (yes/no)")
            if self.args['force'] or uinput == "yes":
                self.write_args_to_conf_file()
        else:
            self.write_args_to_conf_file()


    def write_args_to_conf_file(self):
        print("Writing conf file")
        with open(self.MODULE_CONFIG, "w") as f:
            f.write(json.dumps(self.args))

    def init_env(self):
        self._change_to_module_working_dir()

    def _change_to_module_working_dir(self):
        os.chdir(self.args['path'])
        print("cd'd to " + self.args['path'])


def main():
    return CLIDriver()
