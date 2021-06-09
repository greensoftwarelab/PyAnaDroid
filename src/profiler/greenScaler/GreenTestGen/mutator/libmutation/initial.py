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


class Initial:

	test_script=""

	def __init__(self,fyl):
	
		try:
	        	with open(fyl) as f_in:
	        	    for line in f_in:
	        	        Initial.test_script += line
	        	    f_in.close()
	    	except IOError as e:
	        	print(str(e))
	        	sys.exit()
        @staticmethod	

	def get_initial_script():
		return Initial.test_script

	    	

