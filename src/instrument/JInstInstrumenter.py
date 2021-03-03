from src.instrument.AbstractInstrumenter import AbstractInstrumenter
import subprocess
from src.Types import BUILD_SYSTEM, TESTING_APPROACH, TESTING_FRAMEWORK
from src.instrument.Types import INSTRUMENTATION_TYPE, INSTRUMENTATION_STRATEGY

JINST_PATH="/Users/ruirua/repos/Anadroid/resources/jars/jInst.jar"  #loadFromConfig

class JInstInstrumenter(AbstractInstrumenter):
    def __init__(self, mirror_dirname="_TRANSFORMED_", build_system=BUILD_SYSTEM.GRADLE):
        self.mirror_dirname = mirror_dirname
        self.build_system = build_system
        super().__init__()

    def init(self):
        pass

    def instrument(self, app_id, proj_dir, main_manifest, test_manifest_file=None,  test_approach=TESTING_APPROACH.WHITEBOX, test_frame=TESTING_FRAMEWORK.MONKEY, instr_strategy=INSTRUMENTATION_STRATEGY.METHOD_CALL, instr_type=INSTRUMENTATION_TYPE.TEST):
        # e.g java -jar jInst.jar "-gradle" "_TRANSFORMED_" "X" "./demoProjects/N2AppTest" "./demoProjects/N2AppTest/app/src/main/AndroidManifest.xml" "-" "-TestOriented" "-junit" "N2AppTest--uminho.di.greenlab.n2apptest" "blackbox"
        command = "java -jar \"{JInst_jar}\" -{build_system} \"{mir_dir}\" \"X\" \"{proj_dir}\" \"{manif_file}\" \"{test_manif_file}\" -{test_ori} -{test_frame} \"{app_id}\" -{test_approach}".format(
            JInst_jar=JINST_PATH,
            build_system=self.build_system.GRADLE.value.lower(),
            mir_dir=self.mirror_dirname,
            proj_dir=proj_dir,
            manif_file=main_manifest,
            test_manif_file= test_manifest_file if test_manifest_file is not None else "-",
            test_ori=instr_type.value,
            test_frame=test_frame.value,
            app_id=app_id,
            test_approach=test_approach.value.lower()
        )
        print(command)
        pipes = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        std_out, std_err = pipes.communicate()
        print(std_out)
        print(std_err)
        if pipes.returncode != 0:
            print("error")
            err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
            raise Exception(err_msg)
        elif len(std_err):
            return 0

