#
# Agram test
#	
# Copyright (c) 2015 Shaiful Chowdhury
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundationeither version 2 of the Licenseor
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If notsee <http://www.gnu.org/licenses/>.
#

am start -n us.achromaticmetaphor.agram/.MainActivity
sleep 10


#### single word #################
input tap 294 194
sleep 2
input text 'hlloe'
input tap 501 746
sleep 5
input tap 159 1231
sleep 3



input tap 294 194
sleep 2
input text 'kcki'
input tap 501 746
sleep 5
input tap 159 1231
sleep 3


##### Random words #####################
input tap 294 397
sleep 2
input text '10000'
input tap 501 746
sleep 1
input tap 159 1231
sleep 2


##### Contained words #####################
input tap 294 482
sleep 2
input text 'mad'
input tap 501 746
sleep 5
input tap 159 1231
sleep 3


# "Exit" Process
sleep 2
input keyevent HOME
