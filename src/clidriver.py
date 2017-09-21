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
        self.unknown = unknown
        self.version = pkg_resources.require("trs")[0].version
        if self.args['version']:
            self.print_version_and_exit()
        self.args['version'] = self.version

        self.terraform_args = None
        if self.validate_and_load_args():
            self.terraform_args = sys.argv[1:]

        self._change_to_module_working_dir()
        self.trs = terraform_remote_state.TRS(self.args)

        if self.args['red_black']:
            self.red_black()
        else:
            self.trs.setup()
            if unknown:
                print(self.trs.execute_terraform(unknown))

    def red_black(self):
        self.trs.app = "%s-%s" % (self.trs.app, "a")
        if self.trs.get_remote_state_body():
            self.state_to_deploy = "b"
            self.state_to_destroy = "a"
        else:
            self.state_to_deploy = "a"
            self.state_to_destroy = "b"

        self.trs.app = "%s-%s" % (self.args['app'], self.state_to_deploy)
        self.trs.setup()
        if self.trs.get_remote_state_body():
            temp_unknown = list(self.unknown)
            if temp_unknown[0] == "apply":
                temp_unknown[0] = "destroy"
                temp_unknown.append("-var")
                temp_unknown.append("state=%s" % (self.state_to_deploy))
                temp_unknown.append("-force")
                print(self.trs.execute_terraform(temp_unknown))

        print("Going to deploy: " + self.state_to_deploy)
        print("Going to destroy: " + self.state_to_destroy)
        if self.unknown:
            self.unknown.append("-var")
            self.unknown.append("state=%s" % (self.state_to_deploy))
            print(self.trs.execute_terraform(self.unknown))
        self.trs.app = "%s-%s" % (self.args['app'], self.state_to_destroy)
        self.trs.setup()
        if self.unknown[0] == "apply":
            self.unknown[0] = "destroy"
            self.unknown.append("-var")
            self.unknown.append("state=%s" % (self.state_to_destroy))
            self.unknown.append("-force")
            print(self.trs.execute_terraform(self.unknown))


    def print_version_and_exit(self):
        print(self.version)
        sys.exit(0)

    def accept_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--target", help="module path (default: \".\")", default=".", type=str)
        parser.add_argument("--region", help="AWS Region (default: us-east-1)", default="us-east-1", type=str)
        parser.add_argument("--bucket", help="S3 Bucket", type=str)
        parser.add_argument("--app", help="Application Name", type=str)
        parser.add_argument("--env", help="Environment (ie. dev, test, qa, prod)", type=str)
        parser.add_argument("--profile", help="AWS Config Profile (default: default)", default="default", type=str)
        parser.add_argument("--config", help="Path to .trsconf (default: \"./.trsconf\")", default="./.trsconf", type=str)
        parser.add_argument("--red_black", help="Perform a Red Black Deployment", action='store_true')
        parser.add_argument("--auto_version", help="Auto-Increment Terraform Version", action='store_true')
        parser.add_argument("--force", help="Force a TRS conf file update", action='store_true')
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
