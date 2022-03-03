from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import execute_shell_command


class SDKManager(object):
    """Abstract calls to sdkmanager binary.
    Provides methods to enumerate and install platform-tools or build-tools.
    """
    def __init__(self):
        self.executable_name = "sdkmanager"

    def list(self):
        """lists all available and downloadable resources through sdkmanager.
        Returns:
            str: list of resources.
        """
        res = execute_shell_command(f"{self.executable_name} --list")
        if res.validate():
            return res.output.split()

    def is_build_tools_installed(self, build_tools_version):
        """Checks if a given build tools version is installed.
        Args:
            build_tools_version: build tools version to check.

        Returns:
            bool: True if installed, False otherwise.
        """
        res = execute_shell_command(f"{self.executable_name} --list | grep 'build-tools'")
        if res.validate():
            installed_bld_tools = list(
                map(lambda z: DefaultSemanticVersion(z.split("|")[0].split(";")[1].strip()),
                    filter(lambda x: len(x.split("|")) == 4, res.output.splitlines()))
            )
            build_tools_version = DefaultSemanticVersion(build_tools_version) if not isinstance(build_tools_version, DefaultSemanticVersion) else build_tools_version
            return build_tools_version in installed_bld_tools
        return False

    def download_build_tools_version(self, version):
        """downloads a given build tools version.
        Args:
            version: build tools version.
        """
        if not self.is_build_tools_installed(version):
            cmd = f"{self.executable_name} \"build-tools;{str(version)}\""
            execute_shell_command(cmd).validate(Exception(f"Error while downloading build tools version: {version}"))

    def is_platform_tools_installed(self, plat_tools_version):
        """Checks if a given build platform-tools version is installed.
        Args:
            plat_tools_version: platform-tools version to check.

        Returns:
            bool: True if installed, False otherwise.
        """
        res = execute_shell_command(f"{self.executable_name} --list | grep 'platform-tools'")
        if res.validate():
            installed_bld_tools = list(
                map(lambda z: DefaultSemanticVersion(z.split("|")[0].split(";")[1].strip()),
                    filter(lambda x: len(x.split("|")) == 4, res.output.splitlines()))
            )
            plat_tools_version = DefaultSemanticVersion(plat_tools_version) if not isinstance(plat_tools_version, DefaultSemanticVersion) else plat_tools_version
            return plat_tools_version in installed_bld_tools
        return False

    def download_platform_tools_version(self, version):
        """downloads a given platform-tools version.
        Args:
            version: platform-tools version.
        """
        if not self.is_platform_tools_installed(version):
            cmd = f"{self.executable_name} \"platform-tools;{str(version)}\""
            execute_shell_command(cmd).validate(Exception(f"Error while downloading platform tools version: {version}"))

    def get_list_of_available_build_tools(self):
        """lists the available build_tools.
        Returns:
            version_list(:obj:`list` of :obj:`DefaultSemanticVersion`): list of versions.
        """
        version_list = []
        res = execute_shell_command(f"{self.executable_name} --list | grep 'build-tools'")
        if res.validate():
            version_list = list(
                map(lambda z: DefaultSemanticVersion(z.split("|")[0].split(";")[1].strip()),
                    res.output.splitlines()))
        return version_list

    def is_platforms_installed(self, plat_version):
        """Checks if a given build platforms version is installed.
        Args:
            plat_version: platforms version to check.

        Returns:
            bool: True if installed, False otherwise.
        """
        res = execute_shell_command(f"{self.executable_name} --list | grep 'platforms'")
        if res.validate():
            installed_bld_tools = list(
                    filter(lambda x: len(x.split("|")) == 4 and plat_version in x.split("|"[0]), res.output.splitlines())
            )
            return len(installed_bld_tools) > 0
        return False

    def download_platform(self, plat_version):
        """downloads a given platforms  version.
        Args:
            plat_version: platforms version.
        """
        if not self.is_platforms_installed(plat_version):
            cmd = f"{self.executable_name} \"platforms;android-{plat_version}\""
            execute_shell_command(cmd).validate(Exception(f"Error while downloading platforms. version: {plat_version}"))