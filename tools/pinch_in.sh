#!/system/bin/sh
# 双指内收缩小（pinch-in），多点分步。指位中部空地。
DEV=/dev/input/event2
X0=430; Y0=290; X1=850; Y1=430; CX=590; CY=360
STEPS=${1:-14}; DX=${2:-10}
sendevent $DEV 3 47 0
sendevent $DEV 3 57 1001
sendevent $DEV 3 58 2
sendevent $DEV 3 53 $X0
sendevent $DEV 3 54 $Y0
sendevent $DEV 1 330 1
sendevent $DEV 1 325 1
sendevent $DEV 0 0 0
sendevent $DEV 3 47 1
sendevent $DEV 3 57 1002
sendevent $DEV 3 58 2
sendevent $DEV 3 53 $X1
sendevent $DEV 3 54 $Y1
sendevent $DEV 0 0 0
i=1
while [ $i -le $STEPS ]; do
  t=$((i*DX))
  nx0=$((X0 + (CX-X0)*t/300)); ny0=$((Y0 + (CY-Y0)*t/300))
  nx1=$((X1 + (CX-X1)*t/300)); ny1=$((Y1 + (CY-Y1)*t/300))
  sendevent $DEV 3 47 0
  sendevent $DEV 3 53 $nx0
  sendevent $DEV 3 54 $ny0
  sendevent $DEV 0 0 0
  sendevent $DEV 3 47 1
  sendevent $DEV 3 53 $nx1
  sendevent $DEV 3 54 $ny1
  sendevent $DEV 0 0 0
  usleep 40000
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
