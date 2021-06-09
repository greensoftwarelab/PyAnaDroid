# Acrylic Paint drawing test

# Take idle measurement
sleep 10

# Launch App

am start -n org.zakky.memopad/.PadActivity
sleep 10

# emualte escape to continue
input tap 355 1161 
sleep 2

# Draw Image

input swipe 320 300 420 310 
sleep 1
input swipe 420 310 470 360 
sleep 1
input swipe 470 360 610 370 
sleep 1
input swipe 610 370 480 450
sleep 1
input swipe 480 450 260 450 
sleep 1
input swipe 260 450 130 350
sleep 1
input swipe 130 350 270 350
sleep 1
input swipe 270 350 320 300 
sleep 1
input swipe 260 460 120 800
sleep 1
input swipe 370 460 320 900
sleep 1
input swipe 480 460 560 700
sleep 2

sleep 20

# Return home
input keyevent HOME
sleep 13
