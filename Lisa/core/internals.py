import os


class _ConfOptions(object):
    def __init__(self):
        self.config = {}
        self.valid_options = {"print_debug": False, "use_cython": True}
        for k, v in self.valid_options.items():
            if k in os.environ:
                if type(v) == bool:
                    env = os.environ.get(k)
                    self.config[k] = False if env in ['0', 'False'] else True
                else:
                    self.config[k] = type(v)(os.environ.get(k))

    def set(self, option, value):
        if option in self.valid_options:
            self.config[option] = value
        else:
            print("Not a valid option")

    def get(self, option):
        if option in self.valid_options:
            return self.config.get(option, self.valid_options.get(option))
        else:
            print("Not a valid option:")

config_options = _ConfOptions()


def lisa_print(*args, **kwargs):
    import sys
    if not kwargs.get("debug", True) or config_options.get("print_debug"):
        print(*args, end=kwargs.get("end", "\n"))
        sys.stdout.flush()
