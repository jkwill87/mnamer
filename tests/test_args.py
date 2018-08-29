from sys import argv

from mnamer.args import Arguments

from tests import IS_WINDOWS, TestCase, mock_open, patch


def add_params(params):
    if isinstance(params, str):
        params = (params,)
    for param in params:
        argv.append(param)

def reset_params():
    del argv[1:]



class ArgsTestCase(TestCase):
    def setUp(self):
        reset_params()

    @classmethod
    def tearDownClass(cls):
        reset_params()


class TestTargets(ArgsTestCase):

    def testNoTargets(self):
        expected = set()
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)

    def testSingleTarget(self):
        params = expected = ("file_1.txt",)
        expected = set(params)
        add_params(params)
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)

    def testMultipleTargets(self):
        params = ('file_1.txt', 'file_2.txt', 'file_3.txt')
        expected = set(params)
        add_params(params)
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)

    def testMixedArgs(self):
        params = ('--test', 'file_1.txt', 'file_2.txt')
        add_params(params)
        expected = set(params) - {'--test'}
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)
