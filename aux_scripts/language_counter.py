import json
import os
import matplotlib.pyplot as plt
from pylab import *

from textops import find

EXCLUDED_LANGS = {'gitignore', 'Markdown', 'License', 'JSON', 'YAML', 'Prolog', 'Batch', 'Properties File'}


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
        print(lang_info)
        if 'Name' not in lang_info or lang_info['Name'] in EXCLUDED_LANGS:
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
        bp_dict = en_box.boxplot(the_list, self.language_info.keys(), patch_artist=True)
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
        plt.show()

    def gen_langs_boxplots_cc(self):
        fig1, en_box = plt.subplots()
        the_list = [ list(map(lambda z: z['Complexity'], x)) for x in map(lambda t: t['proj_files'], self.language_info.values())]
        print(the_list)
        bp_dict = en_box.boxplot(the_list, self.language_info.keys(), patch_artist=True)
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
        plt.show()


def main():
    lookup_dir = "/Users/ruirua/repos/pyAnaDroid/demoProjects"
    ls = LanguageStats()
    ls.search_and_parse_files_in_dir(lookup_dir, expected_filename="scc.json")
    print(json.dumps(ls.language_info, indent=1))
    ls.gen_langs_boxplots_loc()
    ls.gen_langs_boxplots_cc()


if __name__ == '__main__':
    main()