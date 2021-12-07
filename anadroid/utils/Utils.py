from subprocess import Popen, PIPE, TimeoutExpired
from textops import find

PYNADROID_KEYSTORE_PATH = "resources/keys/pynadroid-releases.keystore"
KEYSTORE_PASSWORD = "pynadroid"

def get_date_str():
    res = execute_shell_command("date +\"%d_%m_%y_%H_%M_%S\"")
    if res.validate(Exception("Unable to get date")):
        return res.output.strip()

def get_apksigner_bin():
    res = execute_shell_command("find $ANDROID_HOME/build-tools/ -name \"apksigner\"")
    if res.validate(Exception("No apksigner found")):
        return res.output.split()[0]
    return "/Users/ruirua/Library/Android/sdk/build-tools/30.0.3/apksigner"

def sign_apk(apk_path):
       # deprecated after api 26: "jarsigner -verbose -sigalg SHA2-256withRSA -digestalg SHA2-256  -keystore {keystore} {apk_path} {key_alias} <<< \"{passwd}\"".format(keystore=PYNADROID_KEYSTORE_PATH,apk_path=apk_path,key_alias=KEY_ALIAS,passwd=PASSWORD)
       signer_bin = get_apksigner_bin()
       cmd = """{signer_bin} sign --ks {keystore_path} {apk_path} <<< {passwd}""".format(
           signer_bin=signer_bin,
           keystore_path=PYNADROID_KEYSTORE_PATH,
           apk_path=apk_path,
           passwd=KEYSTORE_PASSWORD
       )
       res = execute_shell_command(cmd)
       res.validate(Exception("error signing apk "+ apk_path))
       return res


def execute_shell_command(cmd, args=[], timeout=None):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    out = bytes()
    err = bytes()
    #print(command)
    proc = Popen(command, stdout=PIPE, stderr=PIPE,shell=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except TimeoutExpired as e:
        print("command " + cmd + " timed out")
        out = e.stdout if e.stdout is not None else out
        err = e.stderr if e.stderr is not None else err
        proc.kill()
        proc.returncode = 1
    return COMMAND_RESULT(proc.returncode, out.decode("utf-8"), err.decode('utf-8'))


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split("/"))
    res = find(basedir, pattern=pattern, only_files=type_file=='f',only_dirs=type_file=='d' )
    # filter by depth
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split("/")) <= maxdepth + basedir_len, res))

class COMMAND_RESULT(object):
    def __init__(self, res, out, err):
        self.return_code = res
        self.output = out
        self.errors = err

    def validate(self, e=None):
        if int(self.return_code) != 0:
            if len(self.errors) > 2:
                if e is None:
                    print(self)
                    return False
                else:
                    print(self)
                    return False
                    #raise e
            else:
                print(self)
                return True
        else:
            return True

    def __str__(self):
        return str(
            {'return_code': self.return_code,
             'output': self.output,
             'errors': self.errors
             })


def log_to_file(content, filename):
    open(filename, 'w').write(content)
