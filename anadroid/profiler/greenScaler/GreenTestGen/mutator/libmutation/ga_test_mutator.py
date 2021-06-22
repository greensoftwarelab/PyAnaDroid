"""
Copyright 2016 Shaiful Chowdhury, Stephanie Gil (shaiful@ualberta.ca, sgil@ualberta.ca)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import time, os, subprocess, threading
from test import *
from events import *
from test_mutator import *

class GATestMutator(TestMutator):
    
    def increase_coverage(self):
        """
            Tries to increase coverage of current test by mutating
            it until the coverage is higher.
        """
        # Method 1:
        # Create 5 new tests
        tests = [self.generate_test() for i in range(10)]
        tests.sort(reverse=True)

        # Find two highest coverage tests
        highest1 = tests[0] 
        highest2 = tests[1]

        # Combine the two tests and mutate new test a bit
        self.mate_and_mutate(highest1, highest2)

        return

    def mate_and_mutate(self, test1, test2):
        """
            Takes part of one test and combines it with the second test.
            Mutates the new test slightly by replacing 5% of the events.
        """
        script1 = test1.get_script()
        script2 = test2.get_script()
#        old_script = script1[:len(script1)/2] + script2[len(script1)/2:]
        old_script = script1 + script2
        events = old_script.split('\n') 

        # mutate events by replacing 5% of them
        for i in range(int(0.05*(len(events)-1))):
            events[random.randint(0, len(events)-2)] = random.choice(EVENTS)(self.pkg_name).get_command()

        new_script = ""
        for event in events:
            new_script += event

        self.test.set_script(new_script) 

        # get coverage of new test
        self.calculate_coverage(self.test)
        print("\nCoverage calculated. Mutated test = " + str(self.test))
        

    def generate_test(self):
        """
            Generates a new test by mutating the current one
        """
        self.pid = clean_up(self.pkg_name, self.apk)

        new_test = Test(self.test.get_script(), app_pkg=self.pkg_name)
        print("\n=================================================\n")
        print("Creating new test...")

        # add random events
        for i in range(7):
            new_test.add_event(random.choice(EVENTS)(self.pkg_name).get_command())

        print("\nNew test created.") 

        print("\nCalculating new coverage...")

        # get coverage of new test
        self.calculate_coverage(new_test)
        print("\nCoverage calculated. Test = " + str(new_test))

        return new_test

