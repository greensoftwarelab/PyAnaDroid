from enum import Enum

from anadroid.instrument.Types import INSTRUMENTATION_TYPE


class BUILD_SYSTEM(Enum):
    """Enumerates the build systems that can be used to build Android apps."""
    GRADLE = 'Gradle'
    ANT = 'Ant'
    MAVEN = "Maven"
    UNKNOWN = "Unknown"

class TESTING_FRAMEWORK(Enum):
    """Enumerates supported testing frameworks"""
    MONKEY = "Monkey"
    MONKEY_RUNNER = "Monkeyrunner"
    JUNIT = "JUnit"
    RERAN = "RERAN"
    ESPRESSO = "Espresso"
    ROBOTIUM = "Robotium"
    APP_CRAWLER = "Crawler"
    DROIDBOT = "Droidbot"
    CUSTOM = "Custom"
    OTHER = "Other"


class PROFILER(Enum):
    """Enumerates sota energy profilers."""
    TREPN = 'Trepn'
    GREENSCALER = 'GreenScaler'
    PETRA = 'Petra'
    MONSOON = 'Monsoon'
    MANAFA = "E-manafa"
    NONE = "None"


class INSTRUMENTER(Enum):
    """Enumerates sota instrumentation tools."""
    JINST = 'JInst'
    HUNTER = 'Hunter'
    NONE = "None"


class TESTING_APPROACH(Enum):
    """Enumerates the 3 testing approaches."""
    WHITEBOX = "WhiteBox"
    BLACKBOX = "BlackBox"
    GREYBOX = "GreyBox"


class ANALYZER(Enum):
    """Enumerates the supported analyzers"""
    OLD_ANADROID_ANALYZER = 'Old Anadroid Analyzer'
    MANAFA_ANALYZER = 'Manafa Analyzer'


SUPPORTED_TESTING_APPROACHES = {
    TESTING_APPROACH.WHITEBOX
}

SUPPORTED_TESTING_FRAMEWORKS = {
    TESTING_FRAMEWORK.MONKEY,
    TESTING_FRAMEWORK.RERAN,
    TESTING_FRAMEWORK.APP_CRAWLER,
    TESTING_FRAMEWORK.MONKEY_RUNNER
}

SUPPORTED_BUILDING_SYSTEMS = {
    BUILD_SYSTEM.GRADLE
}

SUPPORTED_PROFILERS = {
    PROFILER.TREPN,
    PROFILER.MANAFA
}

SUPPORTED_INSTRUMENTERS = {
    INSTRUMENTER.JINST
}

SUPPORTED_ANALYZERS = {
    ANALYZER.OLD_ANADROID_ANALYZER,
    ANALYZER.MANAFA_ANALYZER
}

SUPPORTED_INSTRUMENTATION_TYPES = {
    INSTRUMENTATION_TYPE.TEST,
    INSTRUMENTATION_TYPE.ANNOTATION
}