from enum import Enum

from src.instrument.Types import INSTRUMENTATION_TYPE


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

class ANALYZER(Enum):
    ANADROID_ANALYZER = 'Anadroid Analyzer'

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

SUPPORTED_ANALYZERS = {
    ANALYZER.ANADROID_ANALYZER
}

SUPPORTED_INSTRUMENTATION_TYPES = {
    INSTRUMENTATION_TYPE.TEST
}