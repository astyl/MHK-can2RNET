MHK: control wheelchair hack based on the can2RNET project 
================================================
- This hack exploit is part of "the Magic Joystick" project led by a french solidarity association: MyHumanKit - https://myhumankit.org/ 
- It occured during the Fabrikarium hackaton held in Mureaux, october 2019, with collaboration of MyHumanKit & ArianeGroup.
- Big Thanks to the 'can2RNET' creators (Stephen Chavez & Specter) and their contributors to have documented and shared their hack exploit !

TODO move this below to official MHK wiki/github ?

Cahier des charges
======================
Démontrer la faisabilité de prise de controle à distance d'un fauteuil roulant à l'aide d'un appareil externe tel qu'un joystick.

Equipe
======================
- Porteur de projet : Jonathan Menier
- Contributeurs: Florian, Régis, Jonathan, Laetitia, Luc, André, Federico, Julien, Nicolas et Stéphane
- Coordinateur du projet : Stéphane
- Responsable de documentation Margaux Girard

Matériel
=====================
- Raspberry Pi 3 (Model B+) avec Carte SD 2GB
- Carte PiCan2 (non testé) 
- R-Net cable 
- Manette Xbox360

TODO Présenter le schéma d'ensemble (JSM, PM, Raspberry , Pican2)

Installer la raspberry
=====================
1. Mettre en place la raspberry :  
https://www.raspberrypi-france.fr/guide/
2. (Non testé) Installer PiCan2 sur la rasppi3
https://www.elektormagazine.fr/news/avec-pican2-le-raspberry-pi-prend-le-bus-can

TODO: ajouter photo raspberry + pican2

D'après le projet can2rnet, il faudrait ajouter à /boot/config.txt
```
dtparam=spi=on 
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25         
dtoverlay=spi-bcm2835
```

Puis ajouter les lignes suivantes au fichier /etc/network/interfaces.
A noter que le bitrate est fixé à 1250000.
```
allow-hotplug can0
iface can0 can static
        bitrate 125000
        up /sbin/ip link set $IFACE down
        up /sbin/ip link set $IFACE up
```

Puis charger les modules noyaux sous : /etc/modules
```
mcp251x
can_dev
```

Ensuite, redémarrer la Raspberry, puis vérifier que l'interface "can0" est bien montée.
Utiliser la commande `ifconfig`


Mettre en place de la dérivation R-Net entre le fauteuil et la raspberry
==================================
1. Couper et dénuder le cable R-Net.
2. Connecter le cable à la pican2 selon le code couleur suivant:
```
white is can high
blue is can low
black is gnd
red is +vin
```
TODO: ajouter photo du cables (4 pins)
TODO: ajouter photo de la dérivation de Frédérico
TODO: ajouter photo/schéma du système 

Installer l'utilitaire CAN-UTILS (non testé) 
=================================
```
$ git clone https://github.com/linux-can/can-utils
or sudo apt-get install can-utils
```

Superviser & Controler les trames RNET-over-CAN (partiellement testé)  
=========================================
Espionner les trames CAN pendant vos essais de la mise au point, c'est à dire :
- mise sous tension la JSM
- commandes joystick, ...
- activation des voyants, des bips, ... 
 

Avant de passer à la suite, prener le temps de dérouler le scénario suivant et de comprendre la stratégie :
- doc/canPPT.pdf
- doc/RNETdictionary_*.txt 

1. Identifier la trame du heartbeat périodique de la JSM  
- "03c30F0F#8787878787878787" @10Hz

2. Identifier le contrôle XY du joystick (JSM) au power module (PM)  
- "02000000#XxYy" @100Hz (device JSM n°0) 
- "02001000#XxYy" @100Hz (device JSM n°1) 
- ...

3. [Mode JSMError] Mettre la JSM en mode erreur. Envoyer en moins d'une milliseconde au ces trames:
- "0c000000#"
- "0c000000#"
- "0c000000#"
On ne sait pas à quoi cette trame correspond mais elle permet de mettre la JSM en état erreur.
La JSM n'envoie alors plus ses trames de contrôle XY.

Profiter pour envoyer vos trames de controleXY au power module (PM) en vous faisant passer pour le joystick (JSM).
On s'attend à que les roues se mettent à tourner en cohérence de la commande envoyée.

4. [Mode JSMFollow] TODO


Exemples:
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

Démo Manette Xbox360
=========================================
Lancer sur la raspberry `python3 runJSMExploit.py` to control a R-Net based PWC using any usb gamepad connected to the pi3.
Python 3 is required.
