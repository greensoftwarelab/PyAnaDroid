from enum import Enum


class DependencyType(Enum):
    LOCAL_MODULE = "Local Module"
    LOCAL_BINARY = "Local Binary"
    REMOTE = "Remote"
    CLASSPATH = "Classpath"


class BuildDependency(object):
    def __init__(self, name, dep_type=DependencyType.REMOTE, version=None, bin_type=None):
        self.name = name
        self.dep_type = dep_type
        self.version = version
        self.bin_type = bin_type

    def __str__(self):
        return self.name + (" " if  self.version is not None else "")
