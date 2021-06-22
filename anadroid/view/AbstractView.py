from abc import ABC, abstractmethod


class AbstractView(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def show_table(self, table, header=None):
        if header:
            print(header)
        print(table)

    @abstractmethod
    def show_warning(self,warn_type, message):
        print(str(warn_type) + " | " + str(message))

    @abstractmethod
    def show_error(self, err_type, message):
        print(str(err_type) + " | " + str(message))

    @abstractmethod
    def show_info(self, info_type, message):
        print(str(info_type) + " | " + str(message))