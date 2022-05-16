import os
import re
import shutil
from enum import Enum


from termcolor import colored
from textops import grep, cat, echo, sed
from distutils.dir_util import copy_tree
from anadroid.build.SdkManagerWrapper import SDKManager
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import mega_find, get_resources_dir, loge

RES_DIR = get_resources_dir()
GRADLE_RES_DIR = os.path.join(RES_DIR, "build", "gradle")
GRADLE_WRAPPER_DIR = os.path.join(GRADLE_RES_DIR, "wrapper", "gradle")


class KNOWN_ERROR(Enum):
    """Enumerates the list of known gradle build errors that possibly can be fixed the framework."""
    GOOGLE_REPO_ERROR = "method google() for arguments"
    LIBS_ERROR = "No signature of method: java.util.ArrayList.call() is applicable for argument types"
    MIN_SDK_ERROR = "uses-sdk:minSdkVersion (.+) cannot be smaller than version (.+) declared in"
    BUILD_SDK_ERROR = "The SDK Build Tools revision \((.+)\) is too low for project "
    WRAPPER_ERROR = "try editing the distributionUrl"
    WRAPPER_MISMATCH_ERROR = "Failed to notify project evaluation listener"
    WRAPPER_PROP_ERROR = "Wrapper properties file"
    NDK_TOOLCHAIN_ERROR = "NDK toolchains folder"
    BUILD_TOOLS_CPU_ERROR = "Bad CPU type in executable"
    NO_WRAPPER = "Could not find or load main class org.gradle.wrapper.GradleWrapperMain"
    NO_GRADLEW_EXEC = "gradlew: No such file or directory"
    NO_TARGET_PLATFORM = "failed to find target with hash string"
    NO_BUILD_TOOLS = "failed to find Build Tools revision"
    MAYBE_MISSING_GOOGLE_REPO = "Could not resolve all dependencies for configuration"
    USER_HAS_TO_ACCEPT_INSTALL = "INSTALL_FAILED_USER_RESTRICTED"
    NDK_BAD_CONFIG = "did not contain a valid NDK and couldn't be used"
    #UNSUPPORTED_DEPENDENCY_VERSION = "The Android Gradle plugin supports only Butterknife Gradle plugin version 9.0.0-rc2 and higher."


def is_known_error(output):
    """Given the build output, checks if a known error occurred.

    Returns:
        object (obJ:`KNOW_ERROR`): the inferred error. If the error is not known, returns None.
    """
    for error in KNOWN_ERROR:
        is_this_error = error.value in output
        if is_this_error:
            return error
    return None


def solve_known_error(proj, error, error_msg, **kwargs):
    """Tries to fix known build error.
    Args:
        proj(obj:`AndroidProject`): project that raised the error.
        error(obj:`KNOWN_ERROR`):
        error_msg(str): build output containing the error.
    """
    if error == KNOWN_ERROR.WRAPPER_MISMATCH_ERROR:
        #adjust gradle wrapper version
        grad_prop_files = mega_find(proj.proj_dir, "gradle-wrapper.properties", type_file='f')
        bld_gradle_files = proj.get_build_files()
        for f in bld_gradle_files:
            possible_plgin_vers = str(cat(f) | grep("com.android.tools.build:gradle*"))
            has_plg_version = possible_plgin_vers != ""
            if not has_plg_version:
                continue
            plg_version = possible_plgin_vers.split(":")[-1]
            adeq_v = get_adequate_gradle_version(plg_version)
            for fprop in grad_prop_files:
                update_gradle_wrapper_version(fprop, adeq_v)

    elif error == KNOWN_ERROR.NO_WRAPPER:
        # no wrapper config
        copy_tree(GRADLE_WRAPPER_DIR, os.path.join(proj.proj_dir, "gradle"))

    elif error == KNOWN_ERROR.NO_GRADLEW_EXEC:
        shutil.copytree(os.path.join(GRADLE_RES_DIR, "gradlew"), proj.proj_dir)

    elif error == KNOWN_ERROR.NO_TARGET_PLATFORM:
        # extract version -> use sdkmanager to download -> retry
        output = kwargs.get("out") if "out" in kwargs else ""
        current_compileSdkVersion = re.search("android-([0-9]+)",output).groups()[0]
        sdkman = SDKManager()
        sdkman.download_platform(current_compileSdkVersion)

    elif error == KNOWN_ERROR.NO_BUILD_TOOLS:
        # the build tools version being used was not downloaded
        current_build_tools_version = kwargs.get('build-tools')
        SDKManager().download_build_tools_version(current_build_tools_version)

    elif error == KNOWN_ERROR.BUILD_TOOLS_CPU_ERROR:
        # usually this error can be solved by upgrading BuildToolsVersion
        sdkman = SDKManager()
        current_build_tools_version = kwargs.get('build-tools')
        available_build_tools_list = sdkman.get_list_of_available_build_tools()
        new_vers = upgrade_version_from_version_list(available_build_tools_list, current_build_tools_version)
        sdkman.download_build_tools_version(new_vers)
        for bld_file in proj.get_build_files():
            replace_build_tools_version(bld_file, current_build_tools_version, new_vers)

    elif error == KNOWN_ERROR.MAYBE_MISSING_GOOGLE_REPO:
        # add repository in main gradle file
        main_grdl = proj.root_build_file
        add_google_repo(main_grdl)
        has_glu_glu = "google()" in str(cat(proj.root_build_file))
        if not has_glu_glu:
            add_google_repo_build_script(main_grdl)
    elif error == KNOWN_ERROR.MIN_SDK_ERROR:
        pass
        x='''output = kwargs.get("out") if "out" in kwargs else ""
        if output == "":
            return
        tha_manif_file = re.match(r"(.+?AndroidManifest\.xml)", output)
        print(tha_manif_file.groups())
        print(tha_manif_file)'''
    elif error == KNOWN_ERROR.WRAPPER_ERROR:
        # can be solved the same way of WRAPPER_MISMATCH_ERROR
        recom_v = re.search("Minimum supported Gradle version is (.*). Current version", error_msg)
        recom_v = f'{recom_v.groups()[0].strip()}-all' if recom_v else get_adequate_gradle_version(get_gradle_plugin_version(proj.root_build_file))
        grad_prop_files = mega_find(proj.proj_dir, "gradle-wrapper.properties", type_file='f')
        update_gradle_wrapper_version(grad_prop_files[0], recom_v )
        #solve_known_error(proj, error=KNOWN_ERRORS.WRAPPER_MISMATCH_ERROR, **kwargs)

    elif error == KNOWN_ERROR.NDK_BAD_CONFIG:
        loge("BAD NDK configuration. please update ndk path in resources/config/local.properties")
        local_Prop_file = os.path.join(RES_DIR, "config", "local.properties")
        shutil.copy(local_Prop_file, proj.proj_dir)
    elif error == KNOWN_ERROR.GOOGLE_REPO_ERROR:
        # upgrade build tools (min  at least 3.6)
        min = DefaultSemanticVersion("3.6.3")
        current_build_version = get_gradle_plugin_version(proj.root_build_file)
        replace_gradle_plugin_version( proj.root_build_file, current_build_version, min)
        solve_known_error(proj, KNOWN_ERROR.WRAPPER_MISMATCH_ERROR, error_msg, **kwargs)
    #elif error == KNOWN_ERRORS.UNSUPPORTED_DEPENDENCY_VERSION:
    #    pass
    else:
        loge(f"Unable to solve {error}")


def get_adequate_gradle_version(plugin_version):
    """given the gradle plugin version, returns an adequate gradle version to match the plugin version.

    Based on https://developer.android.com/studio/releases/gradle-plugin#updating-gradle table.
    Args:
        plugin_version: Gradle-plugin version.

    Returns:
        version: adequate gradle version.
    """
    version = DefaultSemanticVersion(plugin_version)
    if DefaultSemanticVersion("1.0.0") <= version <= DefaultSemanticVersion("1.1.3"):
        return "2.3-all"
    elif DefaultSemanticVersion("1.2.0") <= version <= DefaultSemanticVersion("1.3.1"):
        return "2.9-all"
    elif DefaultSemanticVersion("1.5.0") == version:
        return "2.13-all"
    elif DefaultSemanticVersion("2.0.0") <= version <= DefaultSemanticVersion("2.1.2"):
        return "2.13-all"
    elif DefaultSemanticVersion("2.1.3") <= version <= DefaultSemanticVersion("2.2.3"):
        return "3.5-all"
    elif DefaultSemanticVersion("2.3.0") <= version < DefaultSemanticVersion("3.0"):
        return "3.3-all"
    elif DefaultSemanticVersion("3.0.0") <= version < DefaultSemanticVersion("3.1.0"):
        return "4.1-all"
    elif DefaultSemanticVersion("3.1.0") <= version < DefaultSemanticVersion("3.2.0"):
        return "4.4-all"
    elif DefaultSemanticVersion("3.2.0") <= version <= DefaultSemanticVersion("3.2.1"):
        return "4.6-all"
    elif DefaultSemanticVersion("3.3.0") <= version <= DefaultSemanticVersion("3.3.3"):
        return "4.10.1-all"
    elif DefaultSemanticVersion("3.4.0") <= version <= DefaultSemanticVersion("3.4.3"):
        return "5.1.1-all"
    elif DefaultSemanticVersion("3.5.0") <= version <= DefaultSemanticVersion("3.5.4"):
        return "5.4.1-all"
    elif DefaultSemanticVersion("3.6.0") <= version <= DefaultSemanticVersion("3.6.4"):
        return "5.6.4-all"
    elif DefaultSemanticVersion("4.0.0") <= version < DefaultSemanticVersion("4.1.0"):
        return "6.1.1-all"
    elif DefaultSemanticVersion("4.2.0") <= version:
        return "6.7.1-all"



def upgrade_version_from_version_list( version_list , upgradable_candidate, opt="max"):
    if opt == "min":
        list_of_bigger_patches = filter(lambda x: x.major == upgradable_candidate.major
                                               and x.minor == upgradable_candidate.minor
                                                    and x.patch > upgradable_candidate.patch,
                                        version_list)
        final_l = sorted(list_of_bigger_patches, key=lambda x: x.patch, reverse=True)
        if len(final_l) > 0:
            return final_l[0]
    else:
        # try major first
        list_of_bigger_majors = filter(lambda x: x.major > upgradable_candidate.major, version_list)
        final_l = list(sorted(set(list_of_bigger_majors), key=lambda x: x.major))

        if len(final_l) > 0:
            return final_l[0]

    # minor version
    list_of_bigger_minors = filter(
        lambda x: x.major == upgradable_candidate.major and x.minor > upgradable_candidate.minor, version_list)
    final_l = sorted(list_of_bigger_minors, key=lambda x: x.minor, reverse=True)
    if len(final_l) > 0:
        return final_l[0]

    if opt == "min":
        # major version
        list_of_bigger_majors = filter(lambda x: x.major > upgradable_candidate.major, version_list)
        final_l = sorted(list_of_bigger_majors, key=lambda x: x.major)

        if len(final_l) > 0:
            return final_l[0]
    else:
        # try major first
        list_of_bigger_patches = filter(lambda
                                            x: x.major == upgradable_candidate.major and x.minor == upgradable_candidate.minor and x.patch > upgradable_candidate.patch,
                                        version_list)
        final_l = sorted(list_of_bigger_patches, key=lambda x: x.patch, reverse=True)
        if len(final_l) > 0:
            return final_l[0]

    return upgradable_candidate


def replace_build_tools_version(bld_file, old_bld_version, new_bld_version):
    """replace build tools version on bld_file gradle file.
    Args:
        bld_file: path of build file.
        old_bld_version: old version.
        new_bld_version: new version.
    """
    old_str = str(old_bld_version)
    new_str = str(new_bld_version)
    new_file = re.sub(old_str, new_str, str(cat(bld_file)))
    with open(bld_file, 'w') as u:
        u.write(new_file)


def replace_gradle_plugin_version(bld_file, old_v, new_v):
    """replace gradle plugin version on bld_file gradle file.
    Args:
        bld_file: path of build file.
        old_v: old version.
        new_v: new version.
    """
    new_file = str(cat(bld_file)).replace(f'com.android.tools.build:gradle:{str(old_v)}', f'com.android.tools.build:gradle:{str(new_v)}')
    with open(bld_file, 'w') as u:
        u.write(new_file)


def add_google_repo(main_grdl):
    """Adds Google as repository to allprojects in main_grdl gradle file.
    Args:
        main_grdl: path of build file.
    """
    file_ctent = str(cat(main_grdl))
    new_file = file_ctent + "\nallprojects {repositories { maven { url 'https://maven.google.com/'\nname 'Google'}}}"
    with open(main_grdl, 'w') as u:
        u.write(new_file)


def add_google_repo_build_script(main_grdl):
    """Adds Google as repository to buildscript block in main_grdl file.
    Args:
        main_grdl: path of build file.
    """
    file_ctent = str(cat(main_grdl))
    new_file = file_ctent + "\nbuildscript {repositories { google() }}"
    with open(main_grdl, 'w') as u:
        u.write(new_file)


def update_gradle_wrapper_version(gradle_wrap_prop_filepath, new_v):
    """updates gradle wrapper version in properties file.
    Args:
        gradle_wrap_prop_filepath: properties file path.
        new_v: new version.
    """
    fl_ctnt = file_content = str(cat(gradle_wrap_prop_filepath))
    current_v = str(echo(fl_ctnt) | grep("distributionUrl=.*")).split("/")[-1].replace("gradle-", "").replace(".zip",                                                                                 "")
    file_content = re.sub(current_v,  new_v, file_content)
    with open(gradle_wrap_prop_filepath, 'w') as u:
        u.write(file_content)


def get_gradle_plugin_version(gradle_file):
    """returns gradle plugin version.
    gets value of com.android.tools.build contained in gradle_file.

    Args:
        gradle_file: build.gradle filepath.

    Returns:
        gradle_plugin_version(str): plugin version.
    """
    gradle_plugin_version = str(cat(gradle_file) | grep("com.android.tools.build") | sed("classpath|com.android.tools.build:gradle:|\"", "")).strip().replace("'","")
    return gradle_plugin_version
