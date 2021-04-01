from subprocess import Popen, PIPE
from textops import find

PYNADROID_KEYSTORE_PATH = "resources/keys/pynadroid-releases.keystore"
#KEY_ALIAS = "anakey"
PASSWORD = "pynadroid"

def get_apksigner_bin():
    return "/Users/ruirua/Library/Android/sdk/build-tools/30.0.3/apksigner"

def sign_apk(apk_path):
       # deprecated after api 26: "jarsigner -verbose -sigalg SHA2-256withRSA -digestalg SHA2-256  -keystore {keystore} {apk_path} {key_alias} <<< \"{passwd}\"".format(keystore=PYNADROID_KEYSTORE_PATH,apk_path=apk_path,key_alias=KEY_ALIAS,passwd=PASSWORD)
       signer_bin = get_apksigner_bin()
       cmd = """{signer_bin} sign --ks {keystore_path} {apk_path} <<< {passwd}""".format(
           signer_bin=signer_bin,
           keystore_path=PYNADROID_KEYSTORE_PATH,
           apk_path=apk_path,
           passwd=PASSWORD
       )
       res, o, e = execute_shell_command(cmd)
       if res != 0 or len(e)> 3:
           print("ERROR SIGNING APK " + apk_path)
       return res

def execute_shell_command(cmd, args=[]):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    proc = Popen(command, stdout=PIPE, stderr=PIPE,shell=True)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8"), err.decode('utf-8')


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split("/"))
    res = find(basedir, pattern=pattern, only_files=type_file=='f',only_dirs=type_file=='d' )
    # filter by depth
    return list(filter(lambda x : basedir_len + mindepth <= len(x.split("/")) <= maxdepth + basedir_len, res))