import re

class DefaultSemanticVersion(object):
    """docstring for DefaultSemanticVersion"""

    def __init__(self, full_version_id):
        super(DefaultSemanticVersion, self).__init__()
        full_version_id = full_version_id.replace("'", "").replace("_", "")
        #print(full_version_id)
        if "-" in full_version_id:
            full_version_id = full_version_id.split("-")[0]
        if re.match(r'^v', full_version_id) or re.match(r'^V', full_version_id):
            full_version_id = re.sub(r'^v', "", full_version_id)
            full_version_id = re.sub(r'^V', "", full_version_id)
        ll = list(filter(lambda x: x != "", full_version_id.split(".")))

        if len(ll) > 1:
            self.major = int(re.sub(r'[a-zA-Z]', "", ll[0]))
            self.minor = int(re.sub(r'[a-zA-Z]', "", ll[1]))
            if len(ll) > 2:
                self.patch = int(''.join(re.findall(r'\d+', ll[2])))
            else:
                self.patch = 0
        else:
            self.major = 0
            self.minor = 0
            self.patch = 0

    def __str__(self):
        return "%d.%d.%d" % (self.major, self.minor, self.patch)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.major == other.major and self.minor == other.minor and self.patch == other.patch

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __lt__(self, other):
        if self.major < other.major:
            return True
        elif self.major == other.major:
            if self.minor < other.minor:
                return True
            elif self.minor == other.minor:
                if self.patch < other.patch:
                    return True
        return False

    def __ge__(self, other):
        return not self.__lt__(other)

    def __gt__(self, other):
        return not self.__eq__(other) and self.__ge__(other)

    def __hash__(self):
        return hash((self.major, self.minor, self.patch))
