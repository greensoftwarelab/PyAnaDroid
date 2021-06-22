from enum import Enum


class INSTRUMENTATION_TYPE(Enum):
    METHOD = "MethodOriented"
    TEST = 'TestOriented'
    ACTIVITY = 'ActivityOriented',
    ANNOTATION = 'AnnotationOriented'

class INSTRUMENTATION_STRATEGY(Enum):
    ANNOTATION = "Annotation"  # insert annotation in classes/methods
    METHOD_CALL = "Method Call"  # insert method calls in procedures
    BLOCK = "Block"  # insert blocks


