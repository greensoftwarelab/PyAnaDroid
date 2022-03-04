from anadroid.testing_framework.work.AbstractWorkLoad import AbstractWorkLoad


class WorkLoad(AbstractWorkLoad):
    def __init__(self):
        """implements Workload functionality by providing a naive way to store work unit to be executed in FIFO order."""
        super(WorkLoad, self).__init__()
        self.work_units = []
        self.w_index = 0

    def add_unit(self, wunit):
        self.work_units.append(wunit)

    def consume(self):
        if len(self.work_units) > self.w_index:
            val = self.work_units[self.w_index]
            self.w_index += 1
            return val
        else:
            return None

    def flush(self):
        self.work_units.clear()
        self.w_index = 0
