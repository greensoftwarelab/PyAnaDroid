from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import execute_shell_command


class SDKManager(object):
    def __init__(self):
        self.executable_name = "sdkmanager"

    def list(self):
        res = execute_shell_command(f"{self.executable_name} --list")
        if res.validate():
            return res.output.split()

    def is_build_tools_installed(self, build_tools_version):
        res = execute_shell_command(f"{self.executable_name} --list | grep 'build-tools'")
        if res.validate():
            installed_bld_tools = list(
                map( lambda z : DefaultSemanticVersion(z.split("|")[0].split(";")[1].strip()) ,
                    filter( lambda x: len(x.split("|")) == 4, res.output.splitlines()))
            )
            build_tools_version = DefaultSemanticVersion(build_tools_version) if not isinstance(build_tools_version, DefaultSemanticVersion) else build_tools_version
            return build_tools_version in installed_bld_tools
        return False

    def download_build_tools_version(self, version):
        if not self.is_build_tools_installed(version):
            cmd = f"{self.executable_name} \"build-tools;{str(version)}\""
            print(cmd)
            execute_shell_command(cmd).validate(Exception(f"Error while downloading build tools version: {version}"))

    def is_platform_tools_installed(self, build_tools_version):
        res = execute_shell_command(f"{self.executable_name} --list | grep 'platform-tools'")
        print(res)
        if res.validate():
            installed_bld_tools = list(
                map(lambda z: DefaultSemanticVersion(z.split("|")[0].split(";")[1].strip()),
                    filter(lambda x: len(x.split("|")) == 4, res.output.splitlines()))
            )
            build_tools_version = DefaultSemanticVersion(build_tools_version) if not isinstance(build_tools_version, DefaultSemanticVersion) else build_tools_version
            return build_tools_version in installed_bld_tools
        return False


    def download_platform_tools_version(self, version):
        if not self.is_platform_tools_installed(version):
            cmd = f"{self.executable_name} \"platform-tools;{str(version)}\""
            print(cmd)
            execute_shell_command(cmd).validate(Exception(f"Error while downloading platform tools version: {version}"))

    def get_list_of_available_build_tools(self):
        version_list = []
        res = execute_shell_command(f"{self.executable_name} --list | grep 'build-tools'")
        if res.validate():
            version_list = list(
                map(lambda z: DefaultSemanticVersion(z.split("|")[0].split(";")[1].strip()),
                    res.output.splitlines()))
        return version_list


    def is_platform_installed(self, plat_version):
        res = execute_shell_command(f"{self.executable_name} --list | grep 'platforms'")
        print(res)
        if res.validate():
            installed_bld_tools = list(
                    filter(lambda x: len(x.split("|")) == 4 and plat_version in x.split("|"[0]), res.output.splitlines())
            )
            return len(installed_bld_tools) > 0
        return False


    def download_platform(self, plat_version):
        if not self.is_platform_installed(plat_version):
            cmd = f"{self.executable_name} \"platforms;android-{plat_version}\""
            execute_shell_command(cmd).validate(Exception(f"Error while downloading platforms. version: {plat_version}"))