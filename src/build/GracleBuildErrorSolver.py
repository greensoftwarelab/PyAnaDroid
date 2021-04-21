from enum import Enum

from textops import grep

to_delete = '''	
googleError=$(grep "method google() for arguments" $logDir/buildStatus.log )
libsError=$(grep "No signature of method: java.util.ArrayList.call() is applicable for argument types: (java.lang.String) values: \[libs\]" $logDir/buildStatus.log)
minSDKerror=$(egrep "uses-sdk:minSdkVersion (.+) cannot be smaller than version (.+) declared in" $logDir/buildStatus.log)
buildSDKerror=$(egrep "The SDK Build Tools revision \((.+)\) is too low for project ':(.+)'. Minimum required is (.+)" $logDir/buildStatus.log)
wrapperError=$(egrep "try editing the distributionUrl" $logDir/buildStatus.log | egrep "gradle-wrapper.properties" )
anotherWrapperError=$(egrep "Wrapper properties file" $logDir/buildStatus.log  )
ndkError=$(grep "NDK toolchains folder" $logDir/buildStatus.log)
buildToolsCPUError=$(grep "Bad CPU type in executable" "$logDir/buildStatus.log" )
(export PATH=$ANDROID_HOME/tools/bin:$PATH)'''


class KNOWN_ERRORS(Enum):
    GOOGLE_REPO_ERROR = "method google() for arguments"
    LIBS_ERROR = "No signature of method: java.util.ArrayList.call() is applicable for argument types"
    MIN_SDK_ERROR = "uses-sdk:minSdkVersion (.+) cannot be smaller than version (.+) declared in"
    BUILD_SDK_ERROR = "The SDK Build Tools revision \((.+)\) is too low for project "
    WRAPPER_ERROR = "try editing the distributionUrl"
    WRAPPER_PROP_ERROR = "Wrapper properties file"
    NDK_TOOLCHAIN_ERROR = "NDK toolchains folder"
    BUILD_TOOLS_CPU_ERROR = "Bad CPU type in executable"

def is_known_error(output):
    for error in KNOWN_ERRORS:
        is_this_error = output | grep(error.value)
        print(is_this_error)
        if is_this_error != "":
            return error
    return None

def solve_known_error(error, proj):
    if error == KNOWN_ERRORS.GOOGLE_REPO_ERROR:
        print("google error")