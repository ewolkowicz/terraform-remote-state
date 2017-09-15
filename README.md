# trs (Terraform Remote State)
A wrapper script to manage terraform state in AWS S3.

#### Description:

trs wraps the whole process of interacting with Terraform and storing state in AWS S3.

trs also handles downloading the right version of terraform for the statefile being worked on or the latest version of terraform. trs can upgrade a statefile which can be useful when doing Red/Black or Blue/Green style deployments.

#### TRS Steps:

1. Initializes S3 bucket with versioning (if necessary)
2. Creates Application directory within bucket and names state file "ENVIRONMENT.tfstate" (if necessary) to organize the management of many applications and versions/environments.
3. Pulls down any state file from S3 for the app/environment.
4. Downloads the corresponding version of terraform to work with the state file.
5. Passes through terraform commands from the trs invocation to the terraform binary.



#### Sample Run:

```
## Create bucket with app -> env.tfvars and then execute "apply --var-file myvars.tfvars"
trs --bucket my-s3-bucket --app cool-app --env dev apply --var-file myvars.tfvars
```

#### TRS Config File:

TRS can use a trsconf file that sets the command line args. This allows you to store a bunch trsconf files in a directory and then specify `trs -c ~/path/to/trsconf apply --var-file my-vars.tfvars` to limit the amount of CLI args while executing terraform commands. The default location is a file named `.trsconf` in the current directory.  


#### Usage:

```
usage: trs [-h] [-t TARGET] [-r REGION] [-b BUCKET] [-a APP] [-e ENV]
           [-p PROFILE] [-c CONFIG] [--auto_version] [-f] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        module path (default: ".")
  -r REGION, --region REGION
                        AWS Region (default: us-east-1)
  -b BUCKET, --bucket BUCKET
                        S3 Bucket
  -a APP, --app APP     Application Name
  -e ENV, --env ENV     Environment (ie. dev, test, qa, prod)
  -p PROFILE, --profile PROFILE
                        AWS Config Profile (default: default)
  -c CONFIG, --config CONFIG
                        Path to .trsconf (default: "./.trsconf")
  --auto_version        Auto-Increment Terraform Version
  -f, --force           Force a TRS conf file update
  -v, --version         Version of trs
  ```
