#!/system/bin/sh
# 双指外扩放大（CoC 地图），多点分步，协议B。只读输入，不读内存。
DEV=/dev/input/event2
# 起点（画面中部空地，避开按钮）
X0=520; Y0=330; X1=760; Y1=390
STEPS=${1:-14}
DX=${2:-10}

# 按下 f0 (slot0)
sendevent $DEV 3 47 0
sendevent $DEV 3 57 1001
sendevent $DEV 3 58 2
sendevent $DEV 3 53 $X0
sendevent $DEV 3 54 $Y0
sendevent $DEV 1 330 1
sendevent $DEV 1 325 1
sendevent $DEV 0 0 0
# 按下 f1 (slot1)
sendevent $DEV 3 47 1
sendevent $DEV 3 57 1002
sendevent $DEV 3 58 2
sendevent $DEV 3 53 $X1
sendevent $DEV 3 54 $Y1
sendevent $DEV 0 0 0

i=1
while [ $i -le $STEPS ]; do
  nx0=$((X0 - i*DX)); ny0=$((Y0 - i*DX))
  nx1=$((X1 + i*DX)); ny1=$((Y1 + i*DX))
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

# 松手
sendevent $DEV 3 47 0
sendevent $DEV 3 57 -1
sendevent $DEV 0 0 0
sendevent $DEV 3 47 1
sendevent $DEV 3 57 -1
sendevent $DEV 0 0 0
sendevent $DEV 1 330 0
sendevent $DEV 1 325 0
sendevent $DEV 0 0 0
