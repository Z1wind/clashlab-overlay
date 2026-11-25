#!/system/bin/sh
# 通用单指 tap（event2 触摸），用法: tap2.sh X Y
DEV=/dev/input/event2
X=$1; Y=$2
sendevent $DEV 3 47 0
sendevent $DEV 3 57 1001
sendevent $DEV 3 53 $X
sendevent $DEV 3 54 $Y
sendevent $DEV 1 330 1
sendevent $DEV 1 325 1
sendevent $DEV 0 0 0
usleep 80000
sendevent $DEV 3 57 -1
sendevent $DEV 1 330 0
sendevent $DEV 1 325 0
sendevent $DEV 0 0 0
