from enum import Enum


class DependencyType(Enum):
    """Represents build dependencies' type."""
    LOCAL_MODULE = "Local Module"
    LOCAL_BINARY = "Local Binary"
    REMOTE = "Remote"
    CLASSPATH = "Classpath"


class BuildDependency(object):
    """Represents an app build dependency referred in build files.

    Attributes:
        name (str): Dependency name.
        dep_type (DependencyType): Type of dependency.
        version (str): Dependency version.
        bin_type (str): Binary type, used when it is a local dependency, such as an .aar.
    """
    def __init__(self, name, dep_type=DependencyType.REMOTE, version=None, bin_type=None):
        """Initializes a BuildDependency instance.

        Args:
            name (str): Dependency name.
            dep_type (DependencyType): Type of dependency.
            version (str): Dependency version.
            bin_type (str): Binary type, used when it is a local dependency, such as an .aar.
        """
        self.name = name
        self.dep_type = dep_type
        self.version = version
        self.bin_type = bin_type

    def __str__(self):
        """Returns a string representation of the BuildDependency.

        Returns:
            str: String representation of the BuildDependency.
        """
        return self.name + (" " if self.version is not None else "")
