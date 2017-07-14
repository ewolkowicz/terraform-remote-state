#!/bin/bash
set -e

module_path="$1"
terraform_bucket_region="$2"
terraform_bucket_name="$3"
application="$4"
environment="$5"

tfstate="s3://$terraform_bucket_name/$application/$environment.tfstate"
tfversion='0.9.11'
cleanup_backend=1

function usage() {
  echo "Description: Sets up remote statefile. Should be run before apply or destroy."
  echo "Usage: terraform.sh [module_path] [bucket_region] [bucket_name] [application] [environment]"
  echo
  echo "module_path:"
  echo " - the path of the terraform module"
  echo
  echo "region:"
  echo " - the aws region (ex. us-east-1)"
  echo
  echo "bucket_name:"
  echo " - name of the s3 bucket to store the state in"
  echo
  echo "Application:"
  echo " - Application/Service Name"
  echo
  echo "Environment:"
  echo " - dev"
  echo " - test"
  echo " - prod"
}

# Ensure script console output is separated by blank line at top and bottom to improve readability
trap echo EXIT
echo

# Validate the input arguments
if [ "$#" -lt 4 ]; then
  usage
  exit 1
fi

# Get the absolute path to the module
if [[ "$module_path" != /* ]]; then
  module_path=$(cd "$(pwd)/$module_path" && pwd)
else
  module_path=$(cd "$module_path" && pwd)
fi

# Clear the .terraform directory (we want to pull the state from the remote)
rm -rf "$module_path/.terraform"

# Make sure we're running in the module directory
cd "$module_path"

# Generate backend.tf config if not already present
if [[ ! -e "backend.tf" ]]; then
  echo "Backend configuration not found, generating now"
  cleanup_backend=0
  cat <<- EOF > backend.tf
    terraform {
      backend "s3" {
        bucket    = "$terraform_bucket_name"
        encrypt   = "true"
      }
    }
EOF
fi


if [[ -z "`aws s3 ls $tfstate`" ]]; then
  echo "No previous state found"
else
  if [[ -z "`aws s3 cp $tfstate - | jq '.modules [] .resources []'`" ]]; then
    aws s3 rm $tfstate
  else
    tfversion="`aws s3 cp $tfstate - | jq '.terraform_version' | tr -d '\"'`"
  fi
fi

if [[ -z "`(./terraform --version | head -n 1 | grep $tfversion) > /dev/null 2>&1`" ]]; then
  if [[ "`uname`" == "Darwin" ]]; then
    bin="darwin_amd64"
  else
    bin="linux_amd64"
  fi

  curl https://releases.hashicorp.com/terraform/$tfversion/terraform_${tfversion}_${bin}.zip > terraform.zip
  unzip -o terraform.zip
  rm terraform.zip
  chmod +x terraform
fi

# Configure remote state storage
./terraform init \
  -backend=true \
  -backend-config="region=$terraform_bucket_region" \
  -backend-config="bucket=$terraform_bucket_name" \
  -backend-config="key=$application/$environment.tfstate" \
  -force-copy -get=true -input=false

# Cleanup
if [[ $cleanup_backend -eq 0 ]]; then
  rm backend.tf
fi
