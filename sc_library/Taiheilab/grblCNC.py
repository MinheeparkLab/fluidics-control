# -*- coding: utf-8 -*-
#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# The basic I/O class for a grbl CNC
# ----------------------------------------------------------------------------------------
#
# author: Taihei Fujimori
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------

import serial
import time

# ----------------------------------------------------------------------------------------
# Grbl CNC Class Definition
# ----------------------------------------------------------------------------------------
class G_CNC():
    def __init__(self,
                 parameters = False):

        # Define attributes
        self.com_port = parameters.get("valves_com_port", "/dev/ttyUSB1")
        self.verbose = parameters.get("verbose", True)
        self.simulate = parameters.get("simulate_valve", False)
        self.serial_verbose = parameters.get("serial_verbose", False)
        
        # Create serial port
        self.serial = serial.Serial(port = self.com_port, baudrate = 115200) # GRBL operates at 115200 baud

        # Define initial valve status
        self.xpos = 'X0'
        self.ypos = 'Y0'
        self.zpos = 'Z0'
        self.feedspeed = 'F2000'
        # wake up grbl, homing and set the home position zero
        self.wakeUp()

    # Wake up grbl
    def wakeUp(self):
        self.sendCommand('\r\n\r\n')
        time.sleep(2)   # Wait for grbl to initialize
        self.serial.flushInput()  # Flush startup text in serial input
        print('MESSAGE -- GRBL woke up.')
        self.sendCommand('$H') # homing
        self.sendCommand('G92 X0 Y0 Z0') # set current position 0
        print('MESSAGE -- Homing is done. Ready to send commands.')
        self.xpos = 'X0'
        self.ypos = 'Y0'
        self.zpos = 'Z0'

    def moveXY(self,newx,newy):
        if self.zpos != 'Z0':
            self.needleUp()
        if self.zpos == 'Z0':
            command = 'G01 '+newx+' '+newy+' '+'Z0'+' '+self.feedspeed
            self.sendCommand(command)
            self.xpos = newx
            self.ypos = newy

    def needleUp(self):
        self.zpos = 'Z0'
        command = 'G01 '+self.xpos+' '+self.ypos+' '+'Z0'+' '+self.feedspeed
        self.sendCommand(command)

    def needleDown(self):
        self.zpos = 'Z-37'
        command = 'G01 '+self.xpos+' '+self.ypos+' '+'Z-37'+' '+self.feedspeed
        self.sendCommand(command)

    def wait(self,waitingtime):
        command = 'G04 P'+str(waitingtime)
        self.sendCommand(command)
        return True

    # Stream g-code to grbl
    def sendCommand(self,command):
        line = command+'\n'
        print('Sending: ' + command)
        self.serial.write(line.encode()) # Send g-code block to grbl
        res = self.getResponse()
        return res

    def getResponse(self):
        grbl_out = self.serial.readline() # Wait for grbl response with carriage return
        return grbl_out.strip().decode()
