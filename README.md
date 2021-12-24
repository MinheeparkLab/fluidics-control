# fluidics-control
stand alone controller of automated fluid handling system.

# Kilroy for MinheeparkLab
This version of kilroy is for minheepark lab ORCA-setup.

In our lab, we use Nikon Inverted ImageExFluorer All-in-one microscopy setup. Thus, connection part to Steve and Dave in Kilroy is not necessary.

Kilroy for minheeparkLab manages protocols by generating hyperprotocol, which is a combination of hybridize protocols and imaging waiting block.

To use it, follow:
 1) set your viewpoints, lambda, z-stack in ImageFluorer ND Acqusition panel.
 
 2) check your imaging part duration.
 
 3) Design your hyperprotocol by inserting hybelist, hybe-ignored, and imaging part duration. Kilroy automatically generates the new hyperprotocol, 
load, and save it.

 4) Start your hyperprotocol with ND Acqusition simultaneously!
 
 
