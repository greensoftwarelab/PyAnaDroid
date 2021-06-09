import unittest, os, subprocess, time, datetime
from test_mutator import TestMutator
from ga_test_mutator import GATestMutator
from events import *
from test import Test
from utils import *

PACKAGE="com.android.calculator2"

def start_app():
    """
        ASSUMES AN EMULATOR HAS ALREADY BEEN STARTED.
        Starts the calculator program, finds the pid, and instantiates a 
        TestMutator object.
    """
    subprocess.call(["adb", "shell", "am start " + PACKAGE])
    time.sleep(10)
    bits = subprocess.check_output('adb shell ps | grep ' + PACKAGE, shell=True)
    pid = bits.split()[1]
    print("Pid is " + pid)
    test = Test("microsleep 10000000\ninput tap 103 719\n", app_pkg=PACKAGE)
    return(TestMutator(test, pid, 700, PACKAGE), GATestMutator(test, pid, 700, PACKAGE))
         
def clean_up():
    """
        Removes files created from tests and closes the calculator app.
    """
    if os.path.isfile("result.txt"):
        os.remove("result.txt")
    if os.path.isfile("run_methods.txt"):
        os.remove("run_methods.txt")
    if os.path.isfile("output.trace"):
        os.remove("output.trace")

class TestMutatorTest(unittest.TestCase):
    
    def test_calculate_coverage(self):
        """
            Tests retreiving coverage of a test. 
            ASSUMES AN EMULATOR HAS ALREADY BEEN STARTED.
        """
        mutator = start_app()[0] 

        if (os.path.isfile("output.trace")):
            os.remove("output.trace")
        
        mutator.calculate_coverage(mutator.test)
        self.assertTrue(os.path.isfile(os.getcwd()+"/output.trace"))
        self.assertIsNotNone(mutator.test.get_coverage())
        self.assertTrue(mutator.test.get_coverage() > 0, str(mutator.test.get_coverage()))

        # clean up
        mutator.test.delete()
        clean_up()

    def test_generate_test(self):
        """
            Tests creating a new test by mutating an old one.
            ASSUMES AN EMULATOR HAS ALREADY BEEN STARTED.
        """
        mutator = start_app()[0] 

        new_test = mutator.generate_test()

        self.assertIsNotNone(new_test) 
        self.assertTrue(new_test.get_coverage() >= 1.5)
        self.assertTrue(os.path.isfile(TESTS_PATH +"/"+new_test.get_name()))

        # clean up
        mutator.test.delete()
        new_test.delete()
        clean_up()


class GATestMutatorTest(unittest.TestCase):
    
    def test_mate_and_mutate(self):
        """ 
            ASSUMES AN EMULATOR HAS ALREADY BEEN STARTED.
        """ 
        test1 = Test("input tap 45 45\ninput tap 45 45\ninput tap 45 45\ninput tap 45 45\n", 50, PACKAGE)
        test2 = Test("input tap 65 65\ninput tap 65 65\ninput tap 45 45\ninput tap 45 45\n", 20, PACKAGE)             
        mutator = start_app()[1] 

        mutator.mate_and_mutate(test1, test2)
        print(mutator.test.get_script())
        self.assertTrue(os.path.isfile(TESTS_PATH +"/"+ mutator.test.get_name()))

        self.assertTrue(len(mutator.test.get_script()), len(test1.get_script()))
        self.assertTrue((mutator.test.get_script() not in test1.get_script()) 
                        or (mutator.test.get_script() not in test2.get_script()))
        
        # clean up
        mutator.test.delete()
        clean_up()
        

class TestTest(unittest.TestCase):

    def test_basic_methods(self):
        a = Test("input tap 100 100\n", 25, PACKAGE)
        self.assertTrue("a" in a.get_name())
        self.assertEqual(a.get_coverage(), 25)
        self.assertEqual(a.get_script(), "input tap 100 100\n")
        
        b = Test("microsleep 4000000\n", 45, PACKAGE)
        now = datetime.datetime.fromtimestamp(time.time())
        self.assertTrue(now.strftime('%Y-%m-%d_%H') in b.get_name())

        c = Test("input tap 200 200\ninput tap 50 50\n", 25, "c.sh")
        
        # Testing comparisons
        self.assertTrue(c == a)
        self.assertTrue(a < b)
        self.assertTrue(c >= a)
        self.assertTrue(b > c)
        self.assertTrue(b != a)

        a.set_coverage(80)
        self.assertTrue("80" in a.get_name())
 
        c.add_event("input tap 120 120\n")
        last = c.get_last_event()
        self.assertEqual(last, "input tap 120 120")

        # clean up
        a.delete()

if __name__ == '__main__':
    unittest.main()
    
