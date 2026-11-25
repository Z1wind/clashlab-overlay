#!/system/bin/sh
# 大行程双指内收（pinch-in）：从两侧远距向中心收拢，30 步。
DEV=/dev/input/event2
sendevent $DEV 3 47 0
sendevent $DEV 3 57 1001
sendevent $DEV 3 58 2
sendevent $DEV 3 53 150
sendevent $DEV 3 54 130
sendevent $DEV 1 330 1
sendevent $DEV 1 325 1
sendevent $DEV 0 0 0
sendevent $DEV 3 47 1
sendevent $DEV 3 57 1002
sendevent $DEV 3 58 2
sendevent $DEV 3 53 1130
sendevent $DEV 3 54 590
sendevent $DEV 0 0 0
i=1
while [ $i -le 30 ]; do
  t=$((i*8))
  nx0=$((150 + (640-150)*t/240)); ny0=$((130 + (360-130)*t/240))
  nx1=$((1130 + (640-1130)*t/240)); ny1=$((590 + (360-590)*t/240))
  sendevent $DEV 3 47 0
  sendevent $DEV 3 53 $nx0
  sendevent $DEV 3 54 $ny0
  sendevent $DEV 0 0 0
  sendevent $DEV 3 47 1
  sendevent $DEV 3 53 $nx1
  sendevent $DEV 3 54 $ny1
  sendevent $DEV 0 0 0
  usleep 70000
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
