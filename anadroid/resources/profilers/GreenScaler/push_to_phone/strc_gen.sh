while ! ps | grep -q -i $1; do :; done;
set `ps | grep -i $1`
#su -c strace -f -c -p $2 -o /sdcard/strace.txt
strace -f -c -p $2 -o /sdcard/strace.txt
