# Terraform S3 Remote State Setup
Helper script to manage terraform state files in AWS S3

#### Description: Sets up remote statefile. Should be run before apply or destroy.
When you run this it will setup the path as the same name of the folder of your terraform template.

ex: if you path is /home/user/application/terraform_application then the s3 folder will be called terraform_application

Note:  It's helpful to copy this to one of your ENV paths so you can call it directly.  This was originally designed to be used in a Jenkins pipeline, but can be used locally if needed.



#### Usage: setup-terraform-remote.sh [module_path] [region] [bucket_name] [application] [env]

module_path:
 - the path of the terraform module

region:
 - the region of the s3 bucket (us-east-1 etc..)

bucket_name:
 - the name of the s3 bucket to store the config

application:
 - the name of the application

environment:
  - dev
  - test
  - prod
