import os
import sys
from shutil import copyfile

from androguard.core.analysis.analysis import MethodAnalysis

from anadroid.analysis.ExecutionResultsAnalyzer import ExecutionResultsAnalyzer
from androguard.misc import AnalyzeAPK
import re
import json

from anadroid.utils.Utils import mega_find, logw

knownRetTypes = {
    "V": "Void",
    "Z": "boolean",
    "B": "byte",
    "S": "short",
    "C": "char",
    "I": "int",
    "J": "long",
    "F": "float",
    "D": "double"
}


def inferType(st):
    st = str(st)
    if (len(st) > 0):
        if "[" in st:
            # array . ex: I[]
            return "[" + inferType(st[1:]) + "]"
        if len(st) > 1:
            return parseMethod(st)
        elif st[0] in knownRetTypes:
            return knownRetTypes[st]
    return ""


def parseMethod(full):
    #print(f"full: {full}")
    full = re.sub(r'^\[', '', str(full)).replace(';', '')
    return re.sub(r'^L', '', full).replace("/", ".").replace(r';|_',"")
    #return re.sub(r'^L', '', full).replace("/", ".").replace(";", "").replace("_", "")


def rreplace(mystr, reverse_removal, reverse_replacement):
    return mystr[::-1].replace(reverse_removal, reverse_replacement, 1)[::-1]


def trolhaSep(mystr, separator):
    r = ""
    l = mystr.split(separator)
    for i in range(0, len(l) - 1):
        r += l[i] + separator
    return rreplace(r, separator, "")


def parseDescriptors(descriptor):
    st = "("
    defaultsep = " "
    real = re.search(r"\(.*\)", descriptor)
    if real is not None:
        for s in real.group(0).split(defaultsep):
            x = s.replace("(", "").replace(")", "")
            if len(x) > 0:
                st += inferType(x) + ","
        return rreplace(st, ",", "") + ")"
    else:
        return "()"


def methodDescriptorToJSON(jsonObj, descriptor):
    st = ""
    defaultsep = " "
    descriptor = str(descriptor)
    jsonObj['method_return'] = inferType(descriptor.split(")")[1])
    jsonObj['method_args'] = []
    real = re.search(r"\(.*\)", descriptor)
    if real is not None:
        for s in real.group(0).split(" "):
            rs = s.replace("(", "").replace(")", "")
            if len(rs) > 0:
                jsonObj['method_args'].append(inferType(rs))
    return jsonObj


def parseArgs(descriptor):
    l = []
    defaultsep = " "
    real = re.search(r"\(.*\)", descriptor)
    if real is not None:
        for s in real.group(0).split(defaultsep):
            x = s.replace("(", "").replace(")", "")
            if len(x) > 0:
                l.append(inferType(x))
    return l


def methodAPIStringToJSON(method_string):
    #print(f"metostring {method_string}")
    jsonObj = {}
    z = re.search(r'->.*\)([A-Za-z]|\/)+', method_string)
    if z is not None:
        method_name = z.group(0)
        jsonObj['return'] = inferType(method_name.split(")")[1])
        jsonObj['args'] = []
        l = method_string.split("->")
        if len(l) == 2:
            class_name = parseMethod(l[0])
            #print(f"a classe {class_name}")
            x = method_name.replace("->", "").split("(")
            method_name_s = x[0]
            jsonObj['name'] = parseMethod(class_name + "." + method_name_s)
            jsonObj['args'] = (parseArgs("(" + x[1]))
    return jsonObj


def parseClassName(classname):
    x = re.sub(r'\$[0-9]+', '', classname)
    return re.sub(r'\$', '.', x)


def inferPackage(classname):
    last_tok_list = classname.split('.')[:-1]
    return '.'.join(last_tok_list)


def eval(path, pack):
    fa, d, dx = AnalyzeAPK(path)
    graph = {}
    pack_redefined = pack.replace(".", "/")
    pack_redefined = trolhaSep(pack_redefined, "/")
    for c in dx.find_classes(name=(".*" + pack_redefined + ".*")):
        classe = {}
        class_name = str(parseClassName(parseMethod(c.name)))
        classe['class_name'] = class_name
        # print("classname ->" + c.name)
        classe['class_superclass'] = parseMethod(c.extends)
        classe['class_implemented_ifaces'] = list(map(parseMethod, c.implements))  # parseMethod(c.implements)
        classe['class_fields'] = []
        classe['class_package'] = inferPackage(parseMethod(c.name))
        # print(c)
        for field in c.get_fields():
            classe['class_fields'].append(inferType(field.get_field().get_descriptor()))
        # print("field->"+field.get_field().get_class_name())
        classe['class_methods'] = {}
        m_index = 0
        for m in c.get_methods():
            orig_method = m.get_method()
            # class encodedmethod
            # print(orig_method.get_name() +"limpo :"  + parseMethod(orig_method.get_name()))
            # if re.match(".*"+ trolhaSep(pack_redefined, "/")  +".*", m.get_method().get_class_name()+".*"):
            m_id = {}
            # print(orig_method.get_access_flags_string())
            m_id['method_name'] = (class_name + "->" + str((orig_method.get_name())))
            methodDescriptorToJSON(m_id, orig_method.get_descriptor())
            m_id['method_modifiers'] = orig_method.get_access_flags_string()
            m_id['method_apis'] = []
            m_id['method_class'] = class_name
            try:
                m_id['method_locals'] = orig_method.get_locals()
                m_id['method_length'] = orig_method.get_length()
                m_id['method_nr_instructions'] = len(list(orig_method.get_instructions()))
            except Exception as e:
                m_id['method_length'] = -1
                m_id['method_nr_instructions'] = -1  # len(list(orig_method.get_instructions()))

            str_id = m_id['method_name'] + "#" + str(m_index)
            m_index = m_index + 1
            if len(m.get_xref_to()) > 0:
                classe['class_methods'][str_id] = m_id
            for other_class, callee, offset in m.get_xref_to():
                str_to_consider = str(callee.get_method()) if isinstance(callee, MethodAnalysis) else str(callee)
                m_id['method_apis'].append(methodAPIStringToJSON(str_to_consider))
            classe['class_methods'][str_id] = m_id
        graph[classe['class_name']] = classe
    filename = pack + ".json"
    with open(filename, 'w') as outfile:
        json.dump(graph, outfile, indent=3)
    return filename


class ApkAPIAnalyzer(ExecutionResultsAnalyzer):
    """Defines a basic interface collect metrics of each method defined in an Android Project using Androguard.
    """
    def __init__(self, profiler):
        super(ApkAPIAnalyzer, self).__init__(profiler)

    def eval_app(self, app):
        if app is None:
            return
        if app.apk is None:
            logw(f"Unable to analyze apk of {app.package_name} (Missing APK path).")
            return
        app_methods_candidates = [x for x in mega_find(os.path.join(app.local_res, "all"), type_file='f', maxdepth=1) if
                                  "allMethods.json" not in x and "DS_Store" not in x]
        app_file_exists = len(app_methods_candidates) > 1 # TODO 0
        if not app_file_exists:
            print(f"apk: {app.apk} | name: {app.package_name}")
            filename = eval(app.apk, app.package_name)
            target_dir = os.path.join(app.local_res, "all")
            copyfile(filename, os.path.join(target_dir, os.path.basename(filename)))

    def setup(self, **kwargs):
        pass

    def analyze_app(self, app, **kwargs):
        print("analyzing apk")
        return eval(app.apk, app.package_name)

    def clean(self):
        pass

    def show_results(self, app_list):
        pass

    def get_val_for_filter(self, filter_name, add_data=None):
        return super().get_val_for_filter(filter_name, add_data)

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        if app is None:
            return True
        self.eval_app(app)
        return super().analyze_tests(app, results_dir=results_dir, **kwargs)

    def analyze_test(self, app, test_id, **kwargs):
        self.eval_app(app)
        return super().analyze_test(app, test_id=test_id, **kwargs)

    def validate_test(self, app, arg1, **kwargs):
        if app is None:
            return True
        self.eval_app(app)
        return super().validate_test(app, arg1, **kwargs)

    def validate_filters(self):
        return super().validate_filters()


if __name__ == '__main__':
    apk_path = sys.argv[1]
    apkname = sys.argv[2]
    eval(apk_path, apkname)