import unittest2 as unittest

def parameterize(cls, parameters):
    def single_parameter(func):
        for key, values in parameters.items():
            def inner(self, values=values):
                return func(self, values)
            setattr(cls, "test_"+key, inner)
    return single_parameter


# class ParamClass():
#     @parameterize(SomeTest, parameters={"a":[1, 2, 3], "b":[2, 3, 4]})
#     def test_parameters(self, a):
#         f = Lisa.File("data/v14-1.h5")
#         assert isinstance(f.bunch_profile(), Lisa.core.file.DataContainer)
#         assert len(f.bunch_profile()) == 3
#         assert len


class NumberedSubTests(unittest.TestResult):
    def addSubTest(self, test, subtest, outcome):
        self.testsRun += 1
        # if outcome is not None:
        #     print("F", end='')
        # else:
        #     print(".", end='')
        super(NumberedSubTests, self).addSubTest(test, subtest, outcome)

import sys
# import contextlib
class CustomTestCase(unittest.TestCase):
    # @contextlib.contextmanager
    # def subTest(self, *args, **kwargs):
    #     yield super(CustomTestCase, self).subTest(*args, **kwargs)
    #     if not self._outcome.success:
    #         sys.stdout.write("F")
    #     else:
    #         sys.stdout.write(".")
    #     sys.stdout.flush()
    @classmethod
    def setUpClass(cls):
        print()
        print("Doing", cls.__name__)

    def run(self, test_result=None, result=None):
        self.runs = 0
        if result is not None:
            test_result = result
        if test_result is None:
            test_result = NumberedSubTests()
        elif not hasattr(test_result, "modded"):
            # if hasattr(test_result, 'stream'):
            #     def sprint(*x):
            #         test_result.stream.write(*x)
            #         test_result.stream.flush()
            # else:
            #     sprint = lambda *x: print(*x, end='')
            test_result.modded = True
            if not hasattr(test_result, 'failfast'):
                test_result.failfast = False
            if not hasattr(test_result, "addSubTest"):
                test_result.addSubTest = unittest.TestResult.addSubTest
                test_result.testsRun = 0
            oast = test_result.addSubTest
            # def nast(test, subtest, err):
            def nast(*args, **kwargs):
                test_result.testsRun += 1
                try:
                    return oast(*args, **kwargs)
                except TypeError:
                    if not hasattr(test_result, 'errors'):
                        test_result.errors = []
                    if not hasattr(test_result, 'failures'):
                        test_result.failures = []

                    if not hasattr(test_result, '_exc_info_to_string'):
                        test_result._exc_info_to_string = lambda *args: str(args[1])
                    return oast(test_result, *args, **kwargs)
            test_result.addSubTest = nast
        x = super(CustomTestCase, self).run(test_result)
        # print()
        # sys.stdout.write("\n")
        # sys.stdout.flush()
        return x


