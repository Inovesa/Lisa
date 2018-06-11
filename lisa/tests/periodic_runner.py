import unittest
import os
import sys

# append the top path for the case when there is an installed and non installed version
# sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


if __name__ == "__main__":
    loader = unittest.TestLoader()
    tests = loader.discover(os.path.dirname(__file__))
    suite = unittest.TestSuite()
    suite.addTests(tests)
    result = unittest.TextTestResult(unittest.runner._WritelnDecorator(sys.stdout), "", 2)
    suite.run(result)
    if len(result.errors) > 0:
        for error in result.errors:
            print("Error in", error[0])
            print(error[1])
            print('='*20)
    print("Ran", result.testsRun, "tests")
    sys.exit(0 if result.wasSuccessful() else 3)
