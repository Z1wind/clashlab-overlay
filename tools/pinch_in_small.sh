#!/system/bin/sh
# 小展开距内收：起点(560,330)/(720,390)，向中心收拢，16步。
DEV=/dev/input/event2
sendevent $DEV 3 47 0
sendevent $DEV 3 57 1001
sendevent $DEV 3 58 2
sendevent $DEV 3 53 560
sendevent $DEV 3 54 330
sendevent $DEV 1 330 1
sendevent $DEV 1 325 1
sendevent $DEV 0 0 0
sendevent $DEV 3 47 1
sendevent $DEV 3 57 1002
sendevent $DEV 3 58 2
sendevent $DEV 3 53 720
sendevent $DEV 3 54 390
sendevent $DEV 0 0 0
i=1
while [ $i -le 16 ]; do
  t=$((i*8))
  nx0=$((560 + (640-560)*t/128)); ny0=$((330 + (360-330)*t/128))
  nx1=$((720 + (640-720)*t/128)); ny1=$((390 + (360-390)*t/128))
  sendevent $DEV 3 47 0
  sendevent $DEV 3 53 $nx0
  sendevent $DEV 3 54 $ny0
  sendevent $DEV 0 0 0
  sendevent $DEV 3 47 1
  sendevent $DEV 3 53 $nx1
  sendevent $DEV 3 54 $ny1
  sendevent $DEV 0 0 0
  usleep 60000
  i=$((i+1))
done
sendevent $DEV 3 47 0
sendevent $DEV 3 57 -1
sendevent $DEV 0 0 0
sendevent $DEV 3 47 1
sendevent $DEV 3 57 -1
sendevent $DEV 0 0 0
sendevent $DEV 1 330 0
sendevent $DEV 1 325 0
sendevent $DEV 0 0 0
