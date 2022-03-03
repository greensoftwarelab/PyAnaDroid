from enum import Enum


class INSTRUMENTATION_TYPE(Enum):
    """Enumerate the type of instrumentation that can be performed"""
    METHOD = "MethodOriented"
    TEST = 'TestOriented'
    ACTIVITY = 'ActivityOriented',
    ANNOTATION = 'AnnotationOriented'
    NONE = "None"


class INSTRUMENTATION_STRATEGY(Enum):
    """Enumerate the instrumentation strategies that can be applied"""
    ANNOTATION = "Annotation"  # insert annotation in classes/methods
    METHOD_CALL = "Method Call"  # insert method calls in procedures
    BLOCK = "Block"  # insert blocks


