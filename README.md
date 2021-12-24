# fluidics-control
stand alone controller of automated fluid handling system.

# Kilroy for MinheeparkLab
Kilroy is a controller code for a series of automated flow protocols written by Jeff Moffitt and Alistair Boettiger

This version of kilroy is for minheepark Lab ORCA-setup.

We use Nikon Inverted ImageExFluorer All-in-one microscopy setup. Thus, connection part to Steve and Dave in Kilroy is not necessary; A new scriptmaker is needed for synchronize Nikon and Microfluidics.

Kilroy for minheeparkLab manages protocols by generating hyperprotocol, which is a combination of hybridize protocols and imaging waiting block.

To use it, follow:
 1) set your viewpoints, lambda, z-stack in ImageFluorer ND Acqusition panel.
 
 2) check your imaging part duration.
 
 3) Design your hyperprotocol by inserting hybelist, hybe-ignored, and imaging part duration. Kilroy automatically generates the new hyperprotocol, 
load, and save it.

 4) Start your hyperprotocol with ND Acqusition simultaneously!
 
![캡처](https://user-images.githubusercontent.com/51374854/147337505-4022d6a8-6cfa-4acb-808b-803f4f0fc36a.JPG)
