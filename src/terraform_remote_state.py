#!/usr/bin/env python
import sys
import json
import os
import boto3
import pprint
import sh
import shutil
from . import terraform_install

class TRS(object):

    def __init__(self, args):
        self.region = args['region']
        self.bucket = args['bucket']
        self.app = args['app']
        self.env = args['env']
        self.awsprofile = args['profile']
        self.auto_increment = args['auto_version']

        self.aws_session = boto3.Session(profile_name=self.awsprofile)
        self.s3Client = self.aws_session.client('s3', region_name=self.region)

        self.terraform = terraform_install.TerraformInstall(self.auto_increment)

    def setup(self):
        self.cleanup_previous_state()
        self.generate_backend_conf()
        self.setup_s3_bucket()
        self.check_previous_remote_state()
        self.setup_remote_state()

    def cleanup_previous_state(self):
        if os.path.isdir(".terraform"):
            shutil.rmtree(".terraform")

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
            self.s3Client.head_bucket(Bucket=self.bucket)
        except:
            self.s3Client.create_bucket(Bucket=self.bucket)
            self.s3Client.put_bucket_versioning(
                Bucket=self.bucket,
                VersioningConfiguration={'MFADelete': 'Disabled', 'Status': 'Enabled'}
            )

    def get_remote_state_body(self):
        key = "%s/%s.tfstate" % (self.app, self.env)
        try:
            self.s3Client.head_object(Bucket=self.bucket, Key=key)
            resp = self.s3Client.get_object(Bucket=self.bucket, Key=key)
            jsonState = json.loads(resp['Body'].read())
            if self.is_state_file_empty(jsonState):
                return None
            else:
                return jsonState
        except:
            return None

    def check_previous_remote_state(self):
        key = "%s/%s.tfstate" % (self.app, self.env)
        remote_state_file = self.get_remote_state_body()
        if remote_state_file:
            tf_version_for_state = remote_state_file['terraform_version']
            self.terraform.get_or_install_tf_version(tf_version_for_state)
        else:
            self.s3Client.delete_object(Bucket=self.bucket, Key=key)


    def is_state_file_empty(self, jsonState):
        jsonState = [j['resources'] for j in jsonState['modules']]
        resourceList = [item for sublist in jsonState for item in sublist]
        if len(resourceList) == 0:
            return True
        else:
            return False

    def setup_remote_state(self):
        print(self.execute_terraform("init",
           "-backend=true",
           "-backend-config=region=%s"%(self.region),
           "-backend-config=bucket=%s"%(self.bucket),
           "-backend-config=profile=%s"%(self.awsprofile),
           "-backend-config=key=%s/%s.tfstate"%(self.app, self.env),
           "-force-copy", "-get=true", "-input=false"))

    def execute_terraform(self, *args):
        return self.terraform.exec_terraform(*args)
