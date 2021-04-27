from src.Types import TESTING_FRAMEWORK
from src.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from src.testing_framework.work.MonkeyWorkUnit import MonkeyWorkUnit
from src.testing_framework.work.WorkLoad import WorkLoad

DEFAULT_RESOURCES_DIR = "resources/testingFrameworks/app-crawlwe/"
DEFAULT_SEEDS_FILE = "monkey_seeds.txt"
DEFAULT_CONFIG_FILE = "monkey_cmd.cfg"



class AppCrawlerFramework(AbstractTestingFramework):
    def __init__(self, default_workload=False, resdir=DEFAULT_RESOURCES_DIR):
        super(AppCrawlerFramework, self).__init__(id=TESTING_FRAMEWORK.APP_CRAWLER)
        self.executable_prefix = "java -jar crawl_launcher.jar "
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload(DEFAULT_SEEDS_FILE)

    def init_default_workload(self, seeds_file):
        self.workload = WorkLoad()
        wl_filename = self.res_dir + seeds_file
        config = self.__load_config_file()
        ofile = open(wl_filename, "r")
        for seed in ofile:
            wk = MonkeyWorkUnit(self.executable_prefix)
            wk.config(seed=seed.strip(), **config)
            self.workload.add_unit(wk)
        ofile.close()


    def execute_test(self, package, wunit=None, timeout=None):
        # java -jar "$ANADROID_PATH/src/testingFrameworks/app-crawler/crawl_launcher.jar" --apk-file "$installedAPK" --app-package-name "$package"  --android-sdk "$ANDROID_HOME") > "$test_log_file"
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute(package)

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=DEFAULT_CONFIG_FILE ):
        cfg_file = self.res_dir + cfg_filename
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key,pair = aline.split("=")
            cfg[key] = pair.strip()
        ofile.close()
        return cfg