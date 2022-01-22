pname=$1
pname=$pname"$"
set `ps |grep $pname` 
cat /proc/$2/stat > /sdcard/cpu_jiffy.txt


