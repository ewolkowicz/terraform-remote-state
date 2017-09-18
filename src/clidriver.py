import argparse
import sys
import os
import json
import pkg_resources  # part of setuptools
from . import terraform_remote_state

class CLIDriver(object):

    def __init__(self):

        args, unknown = self.accept_cli_args()

        self.module_config = args.config

        self.args = vars(args)
        self.version = pkg_resources.require("trs")[0].version
        if self.args['version']:
            self.print_version_and_exit()
        self.args['version'] = self.version

        self.terraform_args = None
        if self.validate_and_load_args():
            self.terraform_args = sys.argv[1:]

        self._change_to_module_working_dir()
        self.trs = terraform_remote_state.TRS(self.args)

        if unknown:
            print(self.trs.execute_terraform(unknown))

    def print_version_and_exit(self):
        print(self.version)
        sys.exit(0)

    def accept_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-t", "--target", help="module path (default: \".\")", default=".", type=str)
        parser.add_argument("-r", "--region", help="AWS Region (default: us-east-1)", default="us-east-1", type=str)
        parser.add_argument("-b", "--bucket", help="S3 Bucket", type=str)
        parser.add_argument("-a", "--app", help="Application Name", type=str)
        parser.add_argument("-e", "--env", help="Environment (ie. dev, test, qa, prod)", type=str)
        parser.add_argument("-p", "--profile", help="AWS Config Profile (default: default)", default="default", type=str)
        parser.add_argument("-c", "--config", help="Path to .trsconf (default: \"./.trsconf\")", default="./.trsconf", type=str)
        parser.add_argument("--auto_version", help="Auto-Increment Terraform Version", action='store_true')
        parser.add_argument("-f", "--force", help="Force a TRS conf file update", action='store_true')
        parser.add_argument("--version", help="Version of trs", action='store_true')

        args, unknown = parser.parse_known_args()
        return args, unknown

    def validate_and_load_args(self):
        if not self.args['bucket'] and not self.args['app'] and not self.args['env']:
            if os.path.exists(self.module_config):
                config = open(self.module_config, "r").read()
                self.args = json.loads(config)
                return True
            else:
                parser.error("Must specify --bucket, --app, and --env")
        elif os.path.exists(self.module_config):
            if not self.args['force']:
                uinput = input("You are about to override .tfrconf, continue? (yes/no)")
            if self.args['force'] or uinput == "yes":
                self.write_args_to_conf_file()
            elif uinput != "yes":
                print("Not writing new config, response was not \"yes\"")
        else:
            self.write_args_to_conf_file()
        return False


    def write_args_to_conf_file(self):
        with open(self.module_config, "w") as f:
            f.write(json.dumps(self.args))

    def _change_to_module_working_dir(self):
        os.chdir(self.args['target'])

def main():
    return CLIDriver()
