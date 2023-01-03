import json
import os

from anadroid.Types import TESTING_APPROACH, TESTING_FRAMEWORK, BUILD_SYSTEM, PROFILER, INSTRUMENTER, ANALYZER
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import get_general_config_dir, loge

GENERAL_CONFIG_FILE_NAME = "general_config.json"
RESOURCES_CONFIG_DIR = get_general_config_dir()
CONFIG_FILE = os.path.join(RESOURCES_CONFIG_DIR, GENERAL_CONFIG_FILE_NAME)


def get_general_config(cfg_type, cfg_file=CONFIG_FILE):
    with open(cfg_file, 'r') as jj:
        cfg = json.load(jj)
    if cfg_type not in cfg:
        loge("invalid config type {cfg_type}")
        return {}
    return cfg[cfg_type] #[key] if key in cfg[cfg_type] else None

def set_general_config(cfg_type, cfg_key, cfg_value,  cfg_file=CONFIG_FILE):
    with open(cfg_file, 'r') as jj:
        cfg = json.load(jj)
    if cfg_type is not None and cfg_type not in cfg:
        raise Exception(f"invalid config type {cfg_type}")
    cfg[cfg_type][cfg_key] = cfg_value

    with open(cfg_file, 'w') as jlo:
        json.dump(cfg, jlo)


SUPPORTED_TESTING_APPROACHES = {
    TESTING_APPROACH.WHITEBOX
}

SUPPORTED_TESTING_FRAMEWORKS = {
    TESTING_FRAMEWORK.MONKEY,
    TESTING_FRAMEWORK.RERAN,
    TESTING_FRAMEWORK.APP_CRAWLER,
    TESTING_FRAMEWORK.MONKEY_RUNNER,
    TESTING_FRAMEWORK.JUNIT,
    TESTING_FRAMEWORK.DROIDBOT,
    TESTING_FRAMEWORK.CUSTOM
}

SUPPORTED_BUILDING_SYSTEMS = {
    BUILD_SYSTEM.GRADLE
}

SUPPORTED_PROFILERS = {
    PROFILER.TREPN,
    PROFILER.MANAFA,
    PROFILER.GREENSCALER,
    PROFILER.NONE
}

SUPPORTED_INSTRUMENTERS = {
    INSTRUMENTER.JINST,
    INSTRUMENTER.NONE
}

SUPPORTED_ANALYZERS = {
    ANALYZER.OLD_ANADROID_ANALYZER,
    ANALYZER.MANAFA_ANALYZER
}

SUPPORTED_INSTRUMENTATION_TYPES = {
    INSTRUMENTATION_TYPE.TEST,
    INSTRUMENTATION_TYPE.ANNOTATION,
    INSTRUMENTATION_TYPE.METHOD
}

SUPPORTED_SUITES = {
    PROFILER.TREPN: [INSTRUMENTATION_TYPE.TEST, INSTRUMENTATION_TYPE.METHOD],
    PROFILER.MANAFA: [INSTRUMENTATION_TYPE.ANNOTATION],
    PROFILER.GREENSCALER: [INSTRUMENTATION_TYPE.ANNOTATION],
    PROFILER.NONE: [INSTRUMENTATION_TYPE.NONE, INSTRUMENTATION_TYPE.ANNOTATION, INSTRUMENTATION_TYPE.METHOD, INSTRUMENTATION_TYPE.TEST]
}