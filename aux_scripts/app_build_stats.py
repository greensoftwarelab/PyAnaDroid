import json
import os
from os import listdir

from pylab import *

from textops import find, cat

from anadroid.application.AndroidProject import AndroidProject


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))


def get_project_root_dir(proj_path):
    """infers Android project root directory."""
    has_gradle_right_next = mega_find(proj_path, pattern="build.gradle", maxdepth=4, type_file='f')
    if len(has_gradle_right_next) > 0:
        top_gradle_file = min(has_gradle_right_next, key=len)
        return os.path.dirname(top_gradle_file)
    return None


def is_android_project(dirpath):
    """determines if a given directory is an Android Project.
    looks for settings.gradle files.
    Args:
        dirpath: path of the directory.

    Returns:
        bool: True if file is in diretory, False otherwise.
    """
    return "settings.gradle" in [f for f in listdir(dirpath)]


def load_projects(dirpath):
    """loads Android Projects from a directory containing one or more projects."""
    return_projs = []
    if is_android_project(dirpath):
        potential_projects = [dirpath]
    else:
        potential_projects = list(
            filter(lambda x: os.path.isdir(os.path.join(dirpath, x)), os.listdir(dirpath)))
    for maybe_proj in potential_projects:
        path_dir = os.path.join(dirpath, maybe_proj)
        proj_fldr = get_project_root_dir(path_dir)
        if proj_fldr is not None:
            return_projs.append(proj_fldr)
        else:
            children_dirs = list(filter(lambda x: os.path.isdir(os.path.join(path_dir, x)), os.listdir(path_dir)))
            for child in children_dirs:
                child_path_dir = os.path.join(path_dir, child)
                proj_fldr = get_project_root_dir(child_path_dir)
                if proj_fldr is not None:
                    return_projs.append(proj_fldr)
    return return_projs


def get_avg(l):
    ret_val = None
    try:
        ret_val = average(l)
    except:
        pass
    return ret_val


def to_int(val):
    ret_val = None
    try:
        ret_val = int(val)
    except:
        pass
    return ret_val


def get_sdk_versions(proj):
    mod_files = [ m.build_file for m in proj.modules.values()]
    avg_min_sdk_v = to_int(get_avg(list(map(lambda t: int(re.search(r'minSdkVersion.*?([0-9]+)', str(cat(t))).groups()[0]), filter(lambda f :
                                                                                              re.search('minSdkVersion.*[0-9]+', str(cat(f))), mod_files)))))
    avg_target_sdk = to_int(get_avg(
        list(map(lambda t: int(re.search(r'targetSdkVersion.*?([0-9]+)', str(cat(t))).groups()[0]), filter(lambda f:
                                                                                                        re.search(
                                                                                                            'targetSdkVersion.*[0-9]+',
                                                                                                            str(cat(
                                                                                                                f))),
                                                                                                        mod_files)))))
    compile_sdk_v = to_int(get_avg(
        list(map(lambda t: int(re.search(r'compileSdkVersion.*?([0-9]+)', str(cat(t))).groups()[0]), filter(lambda f:
                                                                                                        re.search(
                                                                                                            'compileSdkVersion.*[0-9]+',
                                                                                                            str(cat(
                                                                                                                f))),
                                                                                                        mod_files)))))

    buildToolsVersion = to_int(get_avg(
        list(map(lambda t: int(re.search(r'buildToolsVersion.*?(\"|\')([0-9]+)\.', str(cat(t))).groups()[1]), filter(lambda f:
                                                                                                        re.search(
                                                                                                            'buildToolsVersion.*[0-9]+',
                                                                                                            str(cat(
                                                                                                                f))),
                                                                                                        mod_files)))))

    return avg_min_sdk_v, avg_target_sdk, compile_sdk_v, buildToolsVersion


def count_dependencies(proj):
    mod_files = [m.build_file for m in proj.modules.values()]
    code_dependencies = sum(list(map(lambda f: len(re.findall('(implementation |compile )',str(cat(f)))), mod_files)))
    test_dependencies = sum(list(map(lambda f: len(re.findall('(testImplementation |testCompile )', str(cat(f)))), mod_files)))
    android_test_dependencies = sum(list(map(lambda f: len(re.findall('(androidTestImplementation |AndroidTestCompile )', str(cat(f)))), mod_files)))
    return code_dependencies, test_dependencies, android_test_dependencies


class AppBuildStats(object):
    def __init__(self):
        self.parsed_proj_info= []

    def process_proj(self, proj: AndroidProject):
        avg_min_sdk_v, avg_target_sdk, compile_sdk_v, build_tools_v = get_sdk_versions(proj)
        d, t, at = count_dependencies(proj)
        proj_info = {
            'proj_name': proj.proj_name,
            'proj_min_sdk': avg_min_sdk_v,
            'proj_target_sdk': avg_target_sdk,
            'proj_compile_sdk': compile_sdk_v,
            'proj_build_tools': build_tools_v,
            'proj_dependencies': d,
            'proj_test_dependencies': t,
            'proj_android_test_dependencies': at,
        }
        self.parsed_proj_info.append(proj_info)

    def get_stats(self):
        avg_min_sdk = int(get_avg(list(map(lambda x: x['proj_min_sdk'], self.parsed_proj_info))))
        avg_target_sdk = int(get_avg(list(map(lambda x: x['proj_target_sdk'], self.parsed_proj_info))))
        avg_compile_sdk = int(get_avg(list(map(lambda x: x['proj_compile_sdk'], self.parsed_proj_info))))
        avg_dep = int(get_avg(list(map(lambda x: x['proj_dependencies'], self.parsed_proj_info))))
        avg_tdep = int(get_avg(list(map(lambda x: x['proj_test_dependencies'], self.parsed_proj_info))))
        avg_atdep = int(get_avg(list(map(lambda x: x['proj_android_test_dependencies'], self.parsed_proj_info))))

        print(f"average minsdk version:{avg_min_sdk}")
        print(f"average targetsdk version:{avg_target_sdk}")
        print(f"average compilesdk version:{avg_compile_sdk}")

        print(f"average code dependencies:{avg_dep}")
        print(f"average test dependencies:{avg_tdep}")
        print(f"average android test dependencies:{avg_atdep}")


def gen_box_plot(key_list, list_of_lists):
    # eg gen_box_plot(['group1', 'group2'], [[1, 2],[3, 4]]):
    fig1, en_box = plt.subplots()
    bp_dict = en_box.boxplot(list_of_lists, key_list, patch_artist=True)
    i = 0
    for line in bp_dict['medians']:
        x, y = line.get_xydata()[1]  # top of median line
        xx, yy = line.get_xydata()[0]
        text(x, y, '%.2f' % y, fontsize=6)  # draw above, centered
        # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
        i = i + 1

    # set colors
    colors = ['lightblue', 'darkkhaki']
    i = 0
    for bplot in bp_dict['boxes']:
        i = i + 1
        bplot.set_facecolor(colors[i % len(colors)])
    xtickNames = plt.setp(en_box, xticklabels=key_list)
    plt.setp(xtickNames, rotation=90, fontsize=5)
    plt.show()


def main(lookup_dir):
    #lookup_dir = "/Users/ruirua/repos/pyAnaDroid/demoProjects"
    proj_dirs = load_projects(lookup_dir)
    projs = [AndroidProject(projname=os.path.basename(p), projdir=p) for p in proj_dirs]
    abs = AppBuildStats()
    for p in projs:
        abs.process_proj(p)
    abs.get_stats()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("error. provide input dir")