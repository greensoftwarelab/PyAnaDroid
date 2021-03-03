from enum import Enum

class BUILD_SYSTEM(Enum):
    GRADLE = 'Gradle'
    ANT = 'Ant'
    MAVEN = "Maven"
    UNKNOWN = "Unknown"

class TESTING_FRAMEWORK(Enum):
    MONKEY = "Monkey"
    MONKEY_RUNNER = "Monkey runner"
    JUNIT = "JUnit"
    RERAN = "RERAN"
    ESPRESSO = "Espresso"
    ROBOTIUM = "Robotium"
    OTHER = "Other"

class PROFILER(Enum):
    TREPN = 'Trepn Profiler'
    GREENSCALER = 'GreenScaler'
    PETRA = 'Petra'
    MONSOON = 'Monsoon'

class INSTRUMENTER(Enum):
    JINST = 'JInst'
    HUNTER = 'Hunter'

class TESTING_APPROACH(Enum):
    WHITEBOX = "WhiteBox"
    BLACKBOX = "BlackBox"
    GREYBOX = "GreyBox"

SUPPORTED_TESTING_APPROACHES = {
    TESTING_APPROACH.WHITEBOX
}

SUPPORTED_TESTING_FRAMEWORKS = {
    TESTING_FRAMEWORK.MONKEY
}

SUPPORTED_BUILDING_SYSTEMS = {
    BUILD_SYSTEM.GRADLE
}

SUPPORTED_PROFILERS = {
    PROFILER.TREPN
}

SUPPORTED_INSTRUMENTERS = {
    INSTRUMENTER.JINST
}

