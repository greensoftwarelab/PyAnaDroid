from src.view.AbstractView import AbstractView
from termcolor import colored

class CLIView(AbstractView):
    def __init__(self):
        self.warn_color = 'yellow'
        self.info_color = 'blue'
        self.err_color = 'red'
        super().__init__()

    def show_table(self, table, header=None):
        super().show_table(table,header)

    def show_warning(self, warn_type, message):
        print(colored(str(warn_type) + " | " + str(message), self.warn_color ))

    def show_error(self, err_type, message):
        print(colored(str(err_type) + " | " + str(message), self.err_color))

    def show_info(self, info_type, message):
        print(colored(str(info_type) + " | " + str(message), self.info_color))