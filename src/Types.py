from enum import Enum

from src.instrument.Types import INSTRUMENTATION_TYPE


class BUILD_SYSTEM(Enum):
    GRADLE = 'Gradle'
    ANT = 'Ant'
    MAVEN = "Maven"
    UNKNOWN = "Unknown"

class TESTING_FRAMEWORK(Enum):
    MONKEY = "Monkey"
    MONKEY_RUNNER = "Monkeyrunner"
    JUNIT = "JUnit"
    RERAN = "RERAN"
    ESPRESSO = "Espresso"
    ROBOTIUM = "Robotium"
    APP_CRAWLER = "APP_CRAWLER"
    DROIDBOT = "DroidBot"
    OTHER = "Other"

class PROFILER(Enum):
    TREPN = 'Trepn Profiler'
    GREENSCALER = 'GreenScaler'
    PETRA = 'Petra'
    MONSOON = 'Monsoon'
    MANAFA = "E-manafa"

class INSTRUMENTER(Enum):
    JINST = 'JInst'
    HUNTER = 'Hunter'

class TESTING_APPROACH(Enum):
    WHITEBOX = "WhiteBox"
    BLACKBOX = "BlackBox"
    GREYBOX = "GreyBox"

class ANALYZER(Enum):
    ANADROID_ANALYZER = 'Anadroid Analyzer'

