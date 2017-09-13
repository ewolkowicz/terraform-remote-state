#!/usr/bin/env python
import sys
import re
import json
import argparse
import pkg_resources  # part of setuptools
import os
import errno
import stat
import boto3
import pprint
import sh
import requests
import platform
import zipfile

class TRS(object):

    TFR_DIR = str(os.path.expanduser('~/.tfr'))
    TEMP = "/temp/"

    def __init__(self, args):
        self.path = os.path.abspath(args.path)
        self.region = args.region
        self.bucket = args.bucket
        self.app = args.app
        self.env = args.env
        self.awsprofile = args.awsprofile
        self.auto_increment = args.auto_version

        try:
            self.terraform_bin = sh.terraform
        except:
            self.terraform_bin = None

        self.aws_session = boto3.Session(profile_name=self.awsprofile)
        self.s3Client = self.aws_session.client('s3', region_name=self.region)

        self.init_tfr_dir()
        self.tfversion = self.get_or_install_tf_version()

        self.change_to_module_working_dir()
        self.cleanup_previous_state()
        self.generate_backend_conf()
        self.setup_s3_bucket()
        self.check_previous_remote_state()

    def init_tfr_dir(self):
        try:
            os.makedirs(self.TFR_DIR + self.TEMP)
        except:
            pass

    def get_or_install_tf_version(self, version=None):
        if version:
            return self.install_terraform(version)
        installed_version = ""
        latest_version = ""
        try:
            version_output = str(sh.terraform("--version"))
        except:
            version_output = ""
        version_regex = "[0-9]+\.[0-9]+\.[0-9]+"
        installed_search = re.search("Terraform v(%s)" % (version_regex), version_output)
        if installed_search:
            installed_version = installed_search.group(1)
        if self.auto_increment or not installed_version:
            latest_version = requests.get("https://api.github.com/repos/hashicorp/terraform/releases/latest").json()['tag_name'][1:]
            if installed_version != latest_version and latest_version:
                return self.install_terraform(latest_version)
        return installed_version

    def install_terraform(self, version):
        print("Installing: " + version)
        platform_str = ""
        if not os.path.exists(self.TFR_DIR + "/" + version + "/" + "terraform"):
            if platform.system() == "Darwin":
                platform_str = "darwin_amd64"
            elif platform.system() == "Linux":
                platform_str = "linux_amd64"
            terraform_url = "https://releases.hashicorp.com/terraform/%s/terraform_%s_%s.zip" % (version, version, platform_str)
            local_filename = "terraform"
            terraform_bin = self._download_file(terraform_url, local_filename + ".zip", version)
        else:
            terraform_bin = self.TFR_DIR + "/" + version + "/" + "terraform"
        self.terraform_bin = sh.Command(terraform_bin)
        print(self.terraform_bin("--version"))


    def _download_file(self, url, local_file, version):
        r = requests.get(url, stream=True)
        temp_version_dir = self.TFR_DIR + self.TEMP + version + "/"
        final_version_dir = self.TFR_DIR + "/" + version + "/"
        temp_zip_loc = temp_version_dir + local_file
        temp_bin_loc = temp_version_dir + local_file[0:len(local_file)-4]
        final_bin_loc = final_version_dir + local_file[0:len(local_file)-4]
        try:
            os.makedirs(final_version_dir)
        except: pass
        try:
            os.makedirs(temp_version_dir)
        except: pass
        with open(temp_zip_loc, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        if ".zip" in local_file:
            with zipfile.ZipFile(temp_zip_loc, 'r') as zip_ref:
                zip_ref.extractall(temp_version_dir)
            os.remove(temp_zip_loc)
        os.rename(temp_bin_loc, final_bin_loc)
        st = os.stat(final_bin_loc)
        os.chmod(final_bin_loc, st.st_mode | stat.S_IEXEC)
        return final_bin_loc

    def cleanup_previous_state(self):
        if os.path.isdir(".terraform"):
            print("deleted .terraform")
            os.rmdir(".terraform")

    def change_to_module_working_dir(self):
        os.chdir(self.path)
        print("cd'd to " + self.path)

    def generate_backend_conf(self):
        if not os.path.isfile("backend.tf"):
            backend_conf_file = open("backend.tf", "w")
            conf_contents = """
            terraform {
              backend "s3" {
                bucket = "%s"
                encrypt = "true"
              }
            }\n
            """ % (self.bucket)
            backend_conf_file.write(conf_contents)
            backend_conf_file.close()

    def setup_s3_bucket(self):
        try:
            s3Client.head_bucket(Bucket=self.bucket)
        except:
            self.s3Client.create_bucket(Bucket=self.bucket)
            self.s3Client.put_bucket_versioning(
                Bucket=self.bucket,
                VersioningConfiguration={'MFADelete': 'Disabled', 'Status': 'Enabled'}
            )

    def check_previous_remote_state(self):
        key = "%s/%s.tfstate" % (self.app, self.env)
        try:
            s3Client.head_object(Bucket=self.bucket, Key=key)
            resp = s3Client.get_object(Bucket=self.bucket, Key=key)
            jsonState = json.loads(resp['Body'].read())
            if self.is_state_file_empty(jsonState):
                s3Client.delete_object(Bucket=self.bucket, Key=key)
            else:
                tf_version_for_state = jsonState['terraform_version']
                if tf_version_for_state != self.tf_version:
                    self.install_terraform(tf_version_for_state)
        except:
            pass

    def is_state_file_empty(self, jsonState):
        jsonState = json.loads(open("teststate.json", 'r').read())
        jsonState = [j['resources'] for j in jsonState['modules']]
        resourceList = []
        for k,v in jsonState[0].items():
            resourceList.append(k)
        if len(resourceList) == 0:
            return True
        else:
            return False



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="module path", default=".", type=str)
    parser.add_argument("-r", "--region", help="AWS Region", default="us-east-1", type=str)
    parser.add_argument("-b", "--bucket", help="S3 Bucket", type=str)
    parser.add_argument("-a", "--app", help="Application Name", type=str)
    parser.add_argument("-e", "--env", help="Environment (ie. dev, test, qa, prod)", type=str)
    parser.add_argument("-ap", "--awsprofile", help="AWS Config Profile", default="default", type=str)
    parser.add_argument("--auto_version", help="Auto-Increment Terraform Version", action='store_true')
    parser.add_argument("-v", "--version", help="Version of toi", action='store_true')

    args = parser.parse_args()

    if args.version:
        version = pkg_resources.require("toi")[0].version
        print(version)
        sys.exit(0)

    if not args.bucket and not args.app and not args.env:
        parser.error("Must specify --bucket, --app, and --env")

    TRS(args)
