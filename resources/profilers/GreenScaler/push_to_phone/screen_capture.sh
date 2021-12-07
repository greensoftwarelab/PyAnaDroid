while ! ps | grep -q -i $1; do :; done;
i=0
while ps | grep -q -i $1; do :
v1="screencap -p /sdcard/screen_shots/screen"
v2=".png"
$v1$i$v2
i=$((i+1))
sleep 1
done;
