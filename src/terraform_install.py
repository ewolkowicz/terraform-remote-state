import os
import stat
import sh
import requests
import platform
import zipfile
import re

class TerraformInstall(object):

    TFR_DIR = str(os.path.expanduser('~/.tfr'))
    TEMP = "/temp/"

    def __init__(self, auto_increment=False):
        self.auto_increment = auto_increment

        try:
            self.terraform_bin = sh.terraform
        except:
            self.terraform_bin = None
        self._init_tfr_dir()
        self.get_or_install_tf_version()

    def _init_tfr_dir(self):
        try:
            os.makedirs(self.TFR_DIR + self.TEMP)
        except:
            pass

    def get_or_install_tf_version(self, version=None):
        if version:
            return self._install_terraform(version)
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
                return self._install_terraform(latest_version)
        return installed_version

    def exec_terraform(self, *args):
        if self.terraform_bin:
            return self.terraform_bin(*args)

    def _install_terraform(self, version):
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
