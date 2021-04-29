






class WorkUnit(object):
    def __init__(self, bin_cmd):
        self.command = bin_cmd
        self.cmd_args = {}


    def execute(self,pkg_name, **kwargs):
        pass

    def config(self, id=None, *args, **kwargs):
        #adb shell monkey -s $monkey_seed -p $package -v --pct-syskeys 0 --ignore-security-exceptions --throttle $delay_bt_events $monkey_nr_events) &> $localDir/monkey$monkey_seed.log)"
        cmd = self.command  + " "
        for k,v in kwargs.items():
            print(k)
        cmd += " ".join(v)

    def export_results(self):
        pass