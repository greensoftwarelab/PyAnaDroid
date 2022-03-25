from anadroid.testing_framework.work.WorkUnit import WorkUnit


class RERANWorkUnit(WorkUnit):
    """extends WorkUnit functionality to adapt it to RERAN framework executions."""
    def __init__(self, bin_cmd):
       super(RERANWorkUnit, self).__init__(bin_cmd)

    def execute(self, device, *args, **kwargs):
        #os.system("adb shell su -c \" /data/local/./replay /data/local/" + filename+ " 0\"" )
        device.execute_command(self.command, shell=True).validate(("Error executing command " + self.command))

    def config(self, device_test_path=None, **kwargs):
        delay = 0 if 'delay' not in kwargs else kwargs['delay']
        self.command = f" {self.command} {device_test_path} {delay}\""

    def export_results(self):
        pass