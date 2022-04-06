import json
import os
from os import listdir
from subprocess import Popen, PIPE, TimeoutExpired

import matplotlib.pyplot as plt
from pylab import *

from textops import find

EXCLUDED_LANGS = {'gitignore', 'Markdown', 'License', 'JSON', 'YAML', 'Prolog', 'Batch', 'Properties File'}
INCLUDED_LANGS = {'Java', 'Python', 'TypeScript', 'JavaScript', 'C', 'C Header', 'C++', 'Kotlin', 'Rust'}


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
    return proc.returncode, out.decode("utf-8"), err.decode('utf-8')


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    # filter by depth
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))


class LanguageStats(object):
    def __init__(self):
        self.language_info = {}
        self.parsed_files = set()

    def add_language_info(self, lang_info):
        #print(lang_info)
        if 'Name' not in lang_info or lang_info['Name'] in EXCLUDED_LANGS or lang_info['Name'] not in INCLUDED_LANGS:
            return
        if lang_info['Name'] in self.language_info:
            # update stats
            self.language_info[lang_info['Name']] = {
                'proj_count': 1 + self.language_info[lang_info['Name']]['proj_count'],
                'total_loc': lang_info['Code'] + self.language_info[lang_info['Name']]['total_loc'],
                'total_cc': lang_info['Complexity'] + self.language_info[lang_info['Name']]['total_cc'],
                'total_files': lang_info['Count'] + self.language_info[lang_info['Name']]['total_files'],
                'proj_files': self.language_info[lang_info['Name']]['proj_files'] + [lang_info]
            }
        else:
            # new entry
            self.language_info[lang_info['Name']] = {
                'proj_count': 1,
                'total_loc': lang_info['Code'],
                'total_cc': lang_info['Complexity'],
                'total_files': lang_info['Count'],
                'proj_files': [lang_info]
            }

    def parse_file(self, filepath):
        info = {}
        with open(filepath, 'r') as jj:
            info = json.load(jj)
        for lang_info in info:
            self.add_language_info(lang_info)
            self.parsed_files.add(filepath)

    def search_and_parse_files_in_dir(self, directory_path, expected_filename="scc.json"):
        file_list = mega_find(directory_path, pattern=expected_filename, type_file='f')
        for filepath in file_list:
            self.parse_file(filepath)

    def gen_langs_boxplots_loc(self):
        fig1, en_box = plt.subplots()
        the_list = [ list(map(lambda z: z['Code'], x)) for x in map(lambda t: t['proj_files'], self.language_info.values())]
        print(the_list)

        bp_dict = en_box.boxplot(x=the_list,
                            notch=False,  # notch shape
                            vert=True,  # vertical box aligmnent
                            sym='ko',  # red circle for outliers
                            patch_artist=True,  # fill with color
                            )
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

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' LoC")
        plt.show()



        x='''
        bp_dict = plt.boxplot(the_list, self.language_info.keys(),  patch_artist=True)
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

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.show()'''

    def gen_langs_boxplots_cc(self):
        fig1, en_box = plt.subplots()
        the_list = [ list(map(lambda z: z['Complexity'], x)) for x in map(lambda t: t['proj_files'], self.language_info.values())]

        bp_dict = en_box.boxplot(x=the_list,
                            notch=False,  # notch shape
                            vert=True,  # vertical box aligmnent
                            sym='ko',  # red circle for outliers
                            patch_artist=True,  # fill with color
                            )
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

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' CC")
        plt.show()

    def gen_langs_boxplots_total_files(self):
        fig1, en_box = plt.subplots()
        the_list = [list(map(lambda z: z['Count'], x)) for x in
                    map(lambda t: t['proj_files'], self.language_info.values())]

        bp_dict = en_box.boxplot(x=the_list,
                                 notch=False,  # notch shape
                                 vert=True,  # vertical box aligmnent
                                 sym='ko',  # red circle for outliers
                                 patch_artist=True,  # fill with color
                                 )
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

        xtickNames = plt.setp(en_box, xticklabels=list(self.language_info.keys()))
        plt.setp(xtickNames, rotation=90, fontsize=5)
        plt.suptitle("All Projects' #Files")
        plt.show()


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


def build_scc_json_for_all_projs(dirpath):
    projs = load_projects(dirpath)
    print(f"total projs: {len(projs)}")
    for pdir in projs:
        res, o, e = execute_shell_command(f"scc {pdir} -f json > {os.path.join(pdir,'scc.json')}")


def main(lookup_dir):
    #lookup_dir = "/Users/ruirua/repos/pyAnaDroid/demoProjects"
    #build_scc_json_for_all_projs(lookup_dir)
    ls = LanguageStats()
    ls.search_and_parse_files_in_dir(lookup_dir, expected_filename="scc.json")
    #print(json.dumps(ls.language_info, indent=1))
    ls.gen_langs_boxplots_loc()
    ls.gen_langs_boxplots_cc()
    ls.gen_langs_boxplots_total_files()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("error. provide input dir")