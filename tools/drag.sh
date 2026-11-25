#!/system/bin/sh
# sendevent 直接拖拽（无fling动量）：press (X0,Y0) → N步线性到 (X1,Y1) → release
# 用法: drag.sh X0 Y0 X1 Y1 STEPS
DEV=/dev/input/event2
X0=${1:-420}; Y0=${2:-220}; X1=${3:-720}; Y1=${4:-220}; STEPS=${5:-12}
sendevent $DEV 3 47 0
sendevent $DEV 3 57 1001
sendevent $DEV 3 58 2
sendevent $DEV 3 53 $X0
sendevent $DEV 3 54 $Y0
sendevent $DEV 1 330 1
sendevent $DEV 1 325 1
sendevent $DEV 0 0 0
i=1
while [ $i -le $STEPS ]; do
  nx=$(( X0 + (X1-X0)*i/STEPS ))
  ny=$(( Y0 + (Y1-Y0)*i/STEPS ))
  sendevent $DEV 3 47 0
  sendevent $DEV 3 53 $nx
  sendevent $DEV 3 54 $ny
  sendevent $DEV 0 0 0
  usleep 60000
  i=$((i+1))
done
sendevent $DEV 3 47 0
sendevent $DEV 3 57 -1
sendevent $DEV 0 0 0
sendevent $DEV 1 330 0
sendevent $DEV 1 325 0
sendevent $DEV 0 0 0
