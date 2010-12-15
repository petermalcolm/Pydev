import os
import sys

try:
    this_file_name = __file__
except NameError:
    # stupid jython. plain old __file__ isnt working for some reason
    import test_runfiles #@UnresolvedImport - importing the module itself
    this_file_name = test_runfiles.__file__
    

desired_runfiles_path = os.path.normpath(os.path.dirname(this_file_name) + "/..")
sys.path.insert(0, desired_runfiles_path)

import pydev_runfiles_unittest
import pydev_runfiles_xml_rpc
import pydevd_io

#remove existing pydev_runfiles from modules (if any), so that we can be sure we have the correct version
if 'pydev_runfiles' in sys.modules:
    del sys.modules['pydev_runfiles']


import pydev_runfiles
import unittest
import tempfile
import re

#this is an early test because it requires the sys.path changed
orig_syspath = sys.path
a_file = pydev_runfiles.__file__
pydev_runfiles.PydevTestRunner(pydev_runfiles.Configuration(files_or_dirs=[a_file]))
file_dir = os.path.dirname(a_file)
assert file_dir in sys.path
sys.path = orig_syspath[:]

#remove it so that we leave it ok for other tests
sys.path.remove(desired_runfiles_path)

class RunfilesTest(unittest.TestCase):
    
    def _setup_scenario(self, path, t_filter=None, tests=None, files_to_tests=None):
        self.MyTestRunner = pydev_runfiles.PydevTestRunner(
            pydev_runfiles.Configuration(
                files_or_dirs=path,
                test_filter=t_filter,
                verbosity=1,
                tests=tests,
                files_to_tests=files_to_tests,
            )
        )
        self.files = self.MyTestRunner.find_import_files()
        self.modules = self.MyTestRunner.find_modules_from_files(self.files)
        self.all_tests = self.MyTestRunner.find_tests_from_modules(self.modules)
        self.filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)

    def setUp(self):
        self.file_dir = [os.path.abspath(os.path.join(desired_runfiles_path, 'tests/samples'))]
        self._setup_scenario(self.file_dir, None)
        
        
    def test_suite_used(self):
        for suite in self.all_tests+self.filtered_tests:
            self.assert_(isinstance(suite, pydev_runfiles_unittest.PydevTestSuite))

    def test_parse_cmdline(self):
        sys.argv = "pydev_runfiles.py ./".split()
        configuration = pydev_runfiles.parse_cmdline()
        self.assertEquals([sys.argv[1]], configuration.files_or_dirs)
        self.assertEquals(2, configuration.verbosity)        # default value
        self.assertEquals(None, configuration.test_filter)   # default value

        sys.argv = "pydev_runfiles.py ../images c:/temp".split()
        configuration = pydev_runfiles.parse_cmdline()
        self.assertEquals(sys.argv[1:3], configuration.files_or_dirs)
        self.assertEquals(2, configuration.verbosity)

        sys.argv = "pydev_runfiles.py --verbosity 3 ../junk c:/asdf ".split()
        configuration = pydev_runfiles.parse_cmdline()
        self.assertEquals(sys.argv[3:], configuration.files_or_dirs)
        self.assertEquals(int(sys.argv[2]), configuration.verbosity)

        sys.argv = "pydev_runfiles.py -f Abc.test_def ./".split()
        configuration = pydev_runfiles.parse_cmdline()
        self.assertEquals([sys.argv[-1]], configuration.files_or_dirs)
        self.assertEquals([sys.argv[2]], configuration.test_filter)

        sys.argv = "pydev_runfiles.py -f Abc.test_def,Mod.test_abc c:/junk/".split()
        configuration = pydev_runfiles.parse_cmdline()
        self.assertEquals([sys.argv[-1]], configuration.files_or_dirs)
        self.assertEquals(sys.argv[2].split(','), configuration.test_filter)

        sys.argv = ('C:\\eclipse-SDK-3.2-win32\\eclipse\\plugins\\org.python.pydev.debug_1.2.2\\pysrc\\pydev_runfiles.py ' + 
                    '--verbosity 1 ' + 
                    'C:\\workspace_eclipse\\fronttpa\\tests\\gui_tests\\calendar_popup_control_test.py ').split()
        configuration = pydev_runfiles.parse_cmdline()
        self.assertEquals([sys.argv[-1]], configuration.files_or_dirs)
        self.assertEquals(1, configuration.verbosity)

        sys.argv = "pydev_runfiles.py --verbosity 1 -f Mod.test_abc c:/junk/ ./".split()
        configuration = pydev_runfiles.parse_cmdline()
        self.assertEquals(sys.argv[5:], configuration.files_or_dirs)
        self.assertEquals(int(sys.argv[2]), configuration.verbosity)
        self.assertEquals([sys.argv[4]], configuration.test_filter)

    
    def test___adjust_python_path_works_for_directories(self):
        orig_syspath = sys.path
        tempdir = tempfile.gettempdir()
        pydev_runfiles.PydevTestRunner(pydev_runfiles.Configuration(files_or_dirs=[tempdir]))
        self.assertEquals(1, tempdir in sys.path)
        sys.path = orig_syspath[:]
    
    
    def test___adjust_python_path_breaks_for_unkown_type(self):
        self.assertRaises(RuntimeError, pydev_runfiles.PydevTestRunner, pydev_runfiles.Configuration(["./LIKE_THE_NINJA_YOU_WONT_FIND_ME.txt"]))

    def test___setup_test_filter(self):
        setup_tf = self.MyTestRunner._PydevTestRunner__setup_test_filter
        self.assertEquals (None, setup_tf(""))
        self.assertEquals (None, setup_tf(None))
        self.assertEquals ([re.compile("test.*")], setup_tf([".*"]))
        self.assertEquals ([re.compile("test.*"), re.compile("test^$")], setup_tf([".*", "^$"]))
    
    def test___is_valid_py_file(self):
        isvalid = self.MyTestRunner._PydevTestRunner__is_valid_py_file
        self.assertEquals(1, isvalid("test.py"))
        self.assertEquals(0, isvalid("asdf.pyc"))
        self.assertEquals(0, isvalid("__init__.py"))
        self.assertEquals(0, isvalid("__init__.pyc"))
        self.assertEquals(1, isvalid("asdf asdf.pyw"))

    def test___unixify(self):
        unixify = self.MyTestRunner._PydevTestRunner__unixify
        self.assertEquals("c:/temp/junk/asdf.py", unixify("c:SEPtempSEPjunkSEPasdf.py".replace('SEP', os.sep)))

    def test___importify(self):
        importify = self.MyTestRunner._PydevTestRunner__importify
        self.assertEquals("temp.junk.asdf", importify("temp/junk/asdf.py"))
        self.assertEquals("asdf", importify("asdf.py"))
        self.assertEquals("abc.def.hgi", importify("abc/def/hgi"))
        
    def test_finding_a_file_from_file_system(self):
        test_file = "simple_test.py"
        self.MyTestRunner.files_or_dirs = [self.file_dir[0] + test_file]
        files = self.MyTestRunner.find_import_files()
        self.assertEquals(1, len(files))
        self.assertEquals(files[0], self.file_dir[0] + test_file)

    def test_finding_files_in_dir_from_file_system(self):
        self.assertEquals(1, len(self.files) > 0)
        for import_file in self.files:
            self.assertEquals(-1, import_file.find(".pyc"))
            self.assertEquals(-1, import_file.find("__init__.py"))
            self.assertEquals(-1, import_file.find("\\"))
            self.assertEquals(-1, import_file.find(".txt"))

    def test___get_module_from_str(self):
        my_importer = self.MyTestRunner._PydevTestRunner__get_module_from_str
        my_os_path = my_importer("os.path", True, 'unused')
        from os import path
        import os.path as path2
        self.assertEquals(path, my_os_path)
        self.assertEquals(path2, my_os_path)
        self.assertNotEquals(__import__("os.path"), my_os_path)
        self.assertNotEquals(__import__("os"), my_os_path)

    def test_finding_modules_from_import_strings(self):
        self.assertEquals(1, len(self.modules) > 0)

    def test_finding_tests_when_no_filter(self):
        # unittest.py will create a TestCase with 0 tests in it
        # since it just imports what is given
        self.assertEquals(1, len(self.all_tests) > 0)
        files_with_tests = [1 for t in self.all_tests if len(t._tests) > 0]
        self.assertNotEquals(len(self.files), len(files_with_tests))
        
    def count_tests(self, tests):
        total = 0
        for t in tests:
            total += t.countTestCases()
        return total

    def test___match(self):
        matcher = self.MyTestRunner._PydevTestRunner__match
        self.assertEquals(1, matcher(None, "aname"))
        self.assertEquals(1, matcher([".*"], "aname"))
        self.assertEquals(0, matcher(["^x$"], "aname"))
        self.assertEquals(0, matcher(["abc"], "aname"))
        self.assertEquals(1, matcher(["abc", "123"], "123"))

    def test_finding_tests_from_modules_with_bad_filter_returns_0_tests(self):
        self._setup_scenario(self.file_dir, ["NO_TESTS_ARE_SURE_TO_HAVE_THIS_NAME"])
        self.assertEquals(0, self.count_tests(self.all_tests))
        
    def test_finding_test_with_unique_name_returns_1_test(self):
        self._setup_scenario(self.file_dir, ["_i_am_a_unique_test_name"])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEquals(1, self.count_tests(filtered_tests))

    def test_finding_test_with_non_unique_name(self):
        self._setup_scenario(self.file_dir, ["_non_unique_name"])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEquals(1, self.count_tests(filtered_tests) > 2)

    def test_finding_tests_with_regex_filters(self):
        self._setup_scenario(self.file_dir, ["_non.*"])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEquals(1, self.count_tests(filtered_tests) > 2)

        self._setup_scenario(self.file_dir, ["^$"])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEquals(0, self.count_tests(filtered_tests))

        self._setup_scenario(self.file_dir, ["_[x]+.*$"])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEquals(1, self.count_tests(filtered_tests) > 0)

        self._setup_scenario(self.file_dir, ["_[x]+.*$", "_non.*"])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEquals(1, self.count_tests(filtered_tests) > 0)

        self._setup_scenario(self.file_dir, ["I$^NVALID_REGE$$$X$#@!"])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEquals(0, self.count_tests(filtered_tests))
        
    def test_matching_tests(self):
        self._setup_scenario(self.file_dir, None, ['StillYetAnotherSampleTest'])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEqual(1, self.count_tests(filtered_tests))
        
        self._setup_scenario(self.file_dir, None, ['SampleTest.test_xxxxxx1'])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEqual(1, self.count_tests(filtered_tests))
        
        self._setup_scenario(self.file_dir, None, ['SampleTest'])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEqual(8, self.count_tests(filtered_tests))
        
        self._setup_scenario(self.file_dir, None, ['AnotherSampleTest.todo_not_tested'])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEqual(1, self.count_tests(filtered_tests))
        
        self._setup_scenario(self.file_dir, None, ['StillYetAnotherSampleTest', 'SampleTest.test_xxxxxx1'])
        filtered_tests = self.MyTestRunner.filter_tests(self.all_tests)
        self.assertEqual(2, self.count_tests(filtered_tests))
        
    def test_xml_rpc_communication(self):
        notifications = []
        class Server:
            
            def __init__(self, notifications):
                self.notifications = notifications
            
            def notifyConnected(self):
                #This method is called at the very start (in runfiles.py), and we do not check this here
                raise AssertionError('Should not be called from the run tests.')
            
            
            def notifyTestsCollected(self, number_of_tests):
                self.notifications.append(('notifyTestsCollected', number_of_tests))
            
            
            def notifyStartTest(self, file, test):
                pass
                
            def notifyTest(self, cond, captured_output, error_contents, file, test, time):
                if error_contents:
                    error_contents = error_contents.splitlines()[-1].strip()
                self.notifications.append(('notifyTest', cond, captured_output.strip(), error_contents, file, test))
                
            def notifyTestRunFinished(self):
                self.notifications.append(('notifyTestRunFinished',))
            
        server = Server(notifications)
        pydev_runfiles_xml_rpc.SetServer(server)
        simple_test = os.path.join(self.file_dir[0], 'simple_test.py')
        simple_test2 = os.path.join(self.file_dir[0], 'simple2_test.py')
        
        files_to_tests = {}
        files_to_tests.setdefault(simple_test , []).append('SampleTest.test_xxxxxx1'        )
        files_to_tests.setdefault(simple_test , []).append('SampleTest.test_xxxxxx2'        )
        files_to_tests.setdefault(simple_test , []).append('SampleTest.test_non_unique_name')
        files_to_tests.setdefault(simple_test2, []).append('YetAnotherSampleTest.test_abc'  )
        
        self._setup_scenario(None, files_to_tests=files_to_tests)
        self.MyTestRunner.verbosity = 2
        
        buf = pydevd_io.StartRedirect(keep_original_redirection=False)
        try:
            self.MyTestRunner.run_tests()
            self.assertEqual(6, len(notifications))
            expected = [
                    ('notifyTestsCollected', 4),
                    ('notifyTest', 'ok', 'non unique name ran', '', simple_test, 'SampleTest.test_non_unique_name'), 
                    ('notifyTest', 'fail', '', 'AssertionError: Fail test 2', simple_test, 'SampleTest.test_xxxxxx1'), 
                    ('notifyTest', 'ok', '', '', simple_test, 'SampleTest.test_xxxxxx2'), 
                    ('notifyTest', 'ok', '', '', simple_test2, 'YetAnotherSampleTest.test_abc'),
                    ('notifyTestRunFinished',),
                ]
            expected.sort()
            notifications.sort()
            self.assertEqual(
                expected,
                notifications
            )
        finally:
            pydevd_io.EndRedirect()
        b = buf.getvalue()
        self.assert_(b.find('Ran 4 tests in ') != -1, 'Found: '+b)
        

        

if __name__ == "__main__":
    #this is so that we can run it frem the jython tests -- because we don't actually have an __main__ module
    #(so, it won't try importing the __main__ module)
    unittest.TextTestRunner().run(unittest.makeSuite(RunfilesTest))
