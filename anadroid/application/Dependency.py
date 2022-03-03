from enum import Enum


class DependencyType(Enum):
    """Represents build dependencies' type.
    """
    LOCAL_MODULE = "Local Module"
    LOCAL_BINARY = "Local Binary"
    REMOTE = "Remote"
    CLASSPATH = "Classpath"


class BuildDependency(object):
    """Represents app build dependency referred on build files.
    Attributes:
        name(str): dependency name.
        dep_type(:obj:`DependencyType`): type of dependency.
        version(str): dependency version.
        bin_type(str): binary type, used when it is a local dependency, such as an .aar.
    """
    def __init__(self, name, dep_type=DependencyType.REMOTE, version=None, bin_type=None):
        self.name = name
        self.dep_type = dep_type
        self.version = version
        self.bin_type = bin_type

    def __str__(self):
        return self.name + (" " if self.version is not None else "")
