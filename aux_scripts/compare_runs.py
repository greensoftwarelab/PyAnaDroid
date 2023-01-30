

"""script to compare runs of tfs"""

import json
import math
import os
from os import listdir
import time
from subprocess import TimeoutExpired, Popen, PIPE

from pylab import *

from textops import find, cat

from anadroid.application.AndroidProject import AndroidProject

TFS_TO_PROCESS = ['Monkey', 'Droidbot']
APP_INSTR = 'Annotation'

def execute_shell_command(cmd, args=[], timeout=None):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    out = bytes()
    err = bytes()
    #print(command)
    proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
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


def to_serializable_instance(val):
    if val is None:
        return None
    if math.isnan(val):
        return None
    else:
        return float(val)

class ExecAppStats(object):
    def __init__(self):
        self.parsed_execs = {}

    def write_to_file(self, out_file):
        with open(out_file, 'w') as jj:
            json.dump(self.parsed_execs, jj)

    def from_file(self, filepath):
        with open(filepath, 'r') as jj:
            self.parsed_execs = json.load(jj)

    def process_app_folder(self, app_res_folder):
        app_diff_execs = filter_only_last_runs(get_app_execs(app_res_folder))
        app_id = os.path.basename(app_res_folder)
        print(f"app {app_id}")
        for tfr, test_folder in app_diff_execs.items():
            self.parsed_execs[tfr] = {} if tfr not in self.parsed_execs else self.parsed_execs[tfr]
            enval, timeval = get_avg_energy_and_time(test_folder)
            self.parsed_execs[tfr][app_id] = {
                'avg_energy': to_serializable_instance(get_avg_test_energy_per_function(test_folder)),
                'avg_coverage': to_serializable_instance(get_avg_test_coverage(test_folder)),
                'errors': (get_avg_test_errors(test_folder)),
                'total_test_energy': to_serializable_instance(enval),
                'total_test_time': to_serializable_instance(timeval)
            }
            #print(self.parsed_execs[tfr][app_id])

    def plot_energy_boxplot_each_tf(self):
        labels = self.parsed_execs.keys()
        ys = [ list(filter(lambda z:  z is not None and not math.isnan(z), [ t['avg_energy'] for t in y.values()])) for x,y in self.parsed_execs.items()]
        '''for x, y in self.parsed_execs.items():
            x = []
            for vals in y.values():    
                x.append(vals['avg_energy'])'''

        print(ys)
        gen_box_plot(labels, ys, title="energy per function")
        ys = [list(filter(lambda z:  z is not None and not math.isnan(z), [ t['total_test_energy'] for t in y.values()])) for x,y in self.parsed_execs.items()]
        gen_box_plot(labels, ys, title="energy")
        ys = [list(filter(lambda z: z is not None and not math.isnan(z), [t['total_test_time'] for t in y.values()]))
              for x, y in self.parsed_execs.items()]
        gen_box_plot(labels, ys, title="time")


    def plot_errors_boxplot_each_tf(self):
        labels = self.parsed_execs.keys()
        anrs = [ list(filter( lambda z: z is not None and not math.isnan(z), [ t['errors']['ANR'] for t in y.values()])) for x,y in self.parsed_execs.items()]
        jexcep = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['JavaException'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        excep = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['Exception'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        nrels = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['NoRelease'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        rls = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['ResourceLeak'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        npis = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['NoProviderInfo'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        pcs = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['ProcessCrash'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        ukns = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['Unknown'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        errors = [list(filter( lambda z: z is not None and not math.isnan(z), [t['errors']['error_tags'] for t in y.values()])) for x, y in self.parsed_execs.items()]
        print(labels)
        gen_box_plot(labels, anrs, title="ANRs")
        gen_box_plot(labels, jexcep, title="JavaException")
        print(f"sem exceps monkey: {len(list(filter(lambda x: x == 0, jexcep[0])))}")
        print(f"sem exceps droidbot: {len(list(filter(lambda x: x == 0, jexcep[1])))}")
        print(f"com exceps monkey: {len(list(filter(lambda x: x != 0, jexcep[0])))}")
        print(f"com exceps droidbot: {len(list(filter(lambda x: x != 0, jexcep[1])))}")
        gen_box_plot(labels, excep, title="Exception")
        gen_box_plot(labels, nrels, title="NoRelease")
        gen_box_plot(labels, rls, title="ResourceLeak")
        gen_box_plot(labels, npis, title="NoProviderInfo")
        gen_box_plot(labels, pcs, title="ProcessCrash")
        gen_box_plot(labels, ukns, title="Unknown")
        print(f"sem erros monkey: {len(list(filter(lambda x: x==0, errors[0])))}")
        print(f"sem erros droidbot: {len(list(filter(lambda x: x == 0, errors[1])))}")
        print(f"com erros monkey: {len(list(filter(lambda x: x != 0, errors[0])))}")
        print(f"com erros droidbot: {len(list(filter(lambda x: x != 0, errors[1])))}")
        gen_box_plot(labels, errors, title="errors")

    def plot_coverage_boxplot_each_tf(self):
        labels = self.parsed_execs.keys()
        ys = [list(filter(lambda z: z is not None and not math.isnan(z), [t['avg_coverage'] for t in y.values()])) for x, y in
              self.parsed_execs.items()]
        '''for x, y in self.parsed_execs.items():
            x = []
            for vals in y.values():    
                x.append(vals['avg_energy'])'''
        gen_box_plot(labels, ys, title="method coverage")


def get_app_execs(app_res_dir):
    l = []
    for x in TFS_TO_PROCESS:
        l += mega_find(app_res_dir, pattern=f'{x}{APP_INSTR}*', maxdepth=4, type_file='d')
    return l


def filter_only_last_runs(runs_list):
    ret_d = {}
    if len(runs_list) == 0:
        return ret_d
    dirname = os.path.dirname(sorted(runs_list, key=len)[0])
    for tf in TFS_TO_PROCESS:
        list_of_dates = list(map(lambda t: time.strptime(os.path.basename(t).split(APP_INSTR)[1], '_%d_%m_%y_%H_%M_%S'), filter(lambda x : tf in x, runs_list)))
        if len(list_of_dates) == 0:
            continue
        list_of_dates.sort()
        reconstructed_path = os.path.join(dirname, f"{tf}{APP_INSTR}{time.strftime('_%d_%m_%y_%H_%M_%S', list_of_dates[-1])}")
        if not os.path.exists(reconstructed_path):
            print(reconstructed_path)
            reconstructed_path = os.path.join(dirname, "oldRuns",
                                              f"{tf}{APP_INSTR}{time.strftime('_%d_%m_%y_%H_%M_%S', list_of_dates[-1])}")

        ret_d[tf] = reconstructed_path
    return ret_d

def gen_box_plot(key_list, list_of_lists, title="ai"):
    # eg gen_box_plot(['group1', 'group2'], [[1, 2],[3, 4]]):
    fig1, en_box = plt.subplots()
    the_list = list_of_lists

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
        text(x, y, '%.4f' % y, fontsize=8)  # draw above, centered
        # text(xx, en_box.get_ylim()[1] * 0.98, '%.2f' % np.average(list_all_samples[i]), color='darkkhaki')
        i = i + 1

        # set colors
    colors = ['lightblue', 'darkkhaki']
    i = 0
    for bplot in bp_dict['boxes']:
        i = i + 1
        bplot.set_facecolor(colors[i % len(colors)])

    xtickNames = plt.setp(en_box, xticklabels=key_list)
    plt.setp(xtickNames, rotation=45, fontsize=8)
    plt.suptitle(title)
    plt.show()

def gen_violin_plot(key_list, list_of_lists, title="ai"):
    # eg gen_box_plot(['group1', 'group2'], [[1, 2],[3, 4]]):
    fig1, en_box = plt.subplots()
    the_list = list_of_lists

    bp_dict = en_box.violinplot(the_list)
        # set colors
    colors = ['lightblue', 'darkkhaki']
    i = 0
    for bplot in bp_dict['bodies']:
        i = i + 1
        bplot.set_facecolor(colors[i % len(colors)])

    xtickNames = plt.setp(en_box, xticklabels=key_list)
    plt.setp(xtickNames, rotation=90, fontsize=10)
    plt.suptitle(title)
    plt.show()


def get_total_methods_of_app(all_dir):
    app_methods = {}
    app_methods_candidates = [x for x in mega_find(os.path.join(all_dir), type_file='f', maxdepth=1) if
                              "allMethods.json" not in x]
    if len(app_methods_candidates) > 0:
        app_methods_file = app_methods_candidates[0]
        with open(app_methods_file, 'r') as j:
            app_methods = json.load(j)
    else:
        #print(all_dir)
        print(f"no app methods found in {all_dir}")
        return {}
    methods = set()
    for da_class, class_obj in app_methods.items():
        if 'class_methods' not in class_obj:
            continue
        for method in class_obj['class_methods'].keys():
            methods.add(method)
    return methods


def read_json(path):
    js = {}
    with open(path, 'r') as jj:
        js = json.load(jj)
    return js

def get_avg_test_coverage(test_folder_path):
    all_dir_base = os.path.dirname(os.path.dirname(test_folder_path)) if "oldRuns" in test_folder_path \
        else os.path.dirname(test_folder_path)
    total_app_m = get_total_methods_of_app(os.path.join(all_dir_base, "all"))
    #print(total_app_m)
    total_app_m_ct = len(total_app_m)
    tests_avg = get_avg([len(read_json(x).keys()) for x in mega_find(test_folder_path, pattern="function*.json",type_file='f', maxdepth=1)])
    if not math.isnan(tests_avg):
        return tests_avg / total_app_m_ct
    return 0


def get_avg_test_energy_per_function(test_folder_path):
    #tests_avg = get_avg([( sum([sum(list(map(lambda y: y['consumption'], t.values()))) for t in read_json(x).values()])) for x in
    #                     mega_find(test_folder_path, pattern="function*.json", type_file='f', maxdepth=1)])
    tests_avg = get_avg(
        [(sum([(list(map(lambda y: y['consumption'], t.values()))) for t in read_json(x).values()])) for x in
                         mega_find(test_folder_path, pattern="function*.json", type_file='f', maxdepth=1)])
    return tests_avg


def get_avg_energy_and_time(test_folder_path):
    bstat, pft, htf = get_last_files_for_emanafa(test_folder_path)
    if bstat is None or pft is None:
        return None, None
    htf_line_str = f' -htf {htf}' if htf is not None else ""
    res, o, e = execute_shell_command(f"emanafa -bts {bstat} -pft {pft} {htf_line_str}")
    if res == 0:
        energy_val = re.search("energy consumed.*", o).group(0).split(' ')[2]
        time_val = re.search("Elapsed time.*", o).group(0).split(' ')[2]
        return float(energy_val), float(time_val)
    return None, None


def get_last_files_for_emanafa(test_folder_path):
    bstats_files = mega_find(test_folder_path, pattern="bstats-*", type_file='f', maxdepth=1)
    bstats_files.sort(key=(lambda t: int(os.path.basename(t).split("-")[1])))
    if len(bstats_files) == 0:
        return None, None, None
    bstat_file = bstats_files[-1]
    bstat_time = os.path.basename(bstat_file).split("-")[1]
    pft_files = mega_find(test_folder_path, pattern=f"trace-{bstat_time}*.systrace", type_file='f', maxdepth=1)
    hunter_files = mega_find(test_folder_path, pattern=f"hunter.log", type_file='f', maxdepth=1)
    return bstat_file, (pft_files[0] if len(pft_files) > 0 else None), (hunter_files[0] if len(hunter_files) > 0 else None)


def get_avg_test_errors(test_folder_path):
    log_resumes_vals = [read_json(x)['known_errors'] for x in mega_find(test_folder_path, pattern="*logresume.json",
                                                                        type_file='f', maxdepth=1)]
    log_errors = [(read_json(x)['errors'] if 'errors' in read_json(x) else {}) for x in
                        mega_find(test_folder_path, pattern="*logresume.json", type_file='f', maxdepth=1)]
    return {
        'ANR':  to_serializable_instance(sum(list(map(lambda x: x['ANR'], log_resumes_vals)))),
        'ProcessCrash': to_serializable_instance(sum(list(map(lambda x: x['ProcessCrash'], log_resumes_vals)))),
        'JavaException': to_serializable_instance( sum(list(map(lambda x: x['JavaException'], log_resumes_vals)))),
        'Unknown': to_serializable_instance(sum(list(map(lambda x: x['Unknown'], log_resumes_vals)))),
        'NoProviderInfo': to_serializable_instance(sum(list(map(lambda x: x['NoProviderInfo'], log_resumes_vals)))),
        'ResourceLeak': to_serializable_instance( sum(list(map(lambda x: x['ResourceLeak'], log_resumes_vals)))),
        'NoRelease': to_serializable_instance(sum(list(map(lambda x: x['NoRelease'], log_resumes_vals)))),
        'Exception': to_serializable_instance(sum(list(map(lambda x: x['Exception'], log_resumes_vals)))),
        'error_tags': to_serializable_instance(sum(list(map(lambda x: sum(list(x.values())), log_errors)))),
    }


def main(lookup_dir):
    #lookup_dir = "/Users/ruirua/repos/pyAnaDroid/anadroid_results"
    app_res_fldrs = [os.path.join(lookup_dir, x) for x in os.listdir(lookup_dir)]
    eas = ExecAppStats()
    #eas.from_file("output.json")
    for app_res_folder in app_res_fldrs:
        eas.process_app_folder(app_res_folder)

    eas.write_to_file("output.json")
    eas.plot_energy_boxplot_each_tf()
    eas.plot_errors_boxplot_each_tf()
    eas.plot_coverage_boxplot_each_tf()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("error. provide input dir")