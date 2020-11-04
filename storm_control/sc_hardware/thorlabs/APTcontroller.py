#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Connect to a Thorlabs KDC101 controllers using pyAPT
https://github.com/qpit/thorlabs_apt
https://pypi.org/project/thorlabs-apt/#description
https://github.com/qpit/thorlabs_apt/blob/master/thorlabs_apt/core.py

Alistair Boettiger, September 2020

V1.1
Adapted from my PI E873 library

Installation:
pip install pyAPT
copy APT.dll from "Thorlabs path \APT Server\" into the pyapt folder in site-packages

Notes: 
This module requires the PIPython library that ships with the PI controllers.
It also requires the path to this library to be added to the python path (see below).
There is probably a more elegant way to do this.
 
"""


from __future__ import print_function
from copy import deepcopy
import storm_control.sc_library.parameters as params

import thorlabs_apt as apt # The key apt lib


class APTcontroller():

    ## __init__
    #
    # Connect to the PI E873 stage.
    #
    #
    def __init__(self, xStageSN = '27003853', yStageSN = '27003868'):   # should become a parameter, see other stages
        print(['Serial numbers x-stage ' ,xStageSN, ' y-stage ',yStageSN])
    
		self.motorX = apt.Motor(xStageSN)
		self.motorY = apt.Motor(yStageSN)
        
        self.wait = 1 # move commands wait for motion to stop
        self.unit_to_um = 1000.0 # needs calibration.  controller reports in mm 
        self.um_to_unit = 1.0/self.unit_to_um


        # Connect to the stage.
        self.good = 1


    ## getStatus
    #
    # @return True/False if we are actually connected to the stage.
    #
    def getStatus(self):
        return self.good

    ## goAbsolute
    #
    # @param x Stage x position in um.
    # @param y Stage y position in um.
    #
    def goAbsolute(self, x, y):
        if self.good:
            X = x * self.um_to_unit
            Y = y * self.um_to_unit
			rangeX = self.motorX.get_stage_axis_info()
			rangeY = self.motorY.get_stage_axis_info()
            if X > rangeX[0] and X < rangeX[1]:
				self.motorX.move_to(X)  # self, value, blocking = False)
            else:
                print('requested move outside max range!')
            if Y > rangeY[0] and Y < rangeY[1]:
				self.motorY.move_to(Y)
            else:
                print('requested move outside max range!')

    ## goRelative
    #
    # @param dx Amount to displace the stage in x in um.
    # @param dy Amount to displace the stage in y in um.
    #
    def goRelative(self, dx, dy):
        if self.good:
            # self.jog(0.0,0.0)
            X =  dx * self.um_to_unit
			Y =  dy * self.um_to_unit
			rangeX = self.motorX.get_stage_axis_info()
			rangeY = self.motorY.get_stage_axis_info()
            if  X > rangeX[0] and X < rangeX[1]:
                self.motorX.move_by(X)
            else:
                print('requested move outside max X range!')
            if  Y > rangeY[0] and Y < rangeY[1]:
                self.motorY.move_by(Y)
            else:
                print('requested move outside max Y range!')
            
            
    ## position   https://github.com/qpit/thorlabs_apt/blob/master/thorlabs_apt/core.py
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def position(self):
        if self.good:
            x0 = self.motorX.position  # query single axis
            y0 = self.motorY.position  # query single axis
            return {"x" : x0,
                "y" : y0}

            
    
    ## jog
    #
    # @param x_speed Speed to jog the stage in x in um/s.  - not clear to me what jog is used for. 
    # @param y_speed Speed to jog the stage in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        pass
        # figure out how to do something here
        # if self.good:
        #     c_xs = c_double(x_speed * self.um_to_unit)
        #     c_ys = c_double(y_speed * self.um_to_unit)
        #     c_zr = c_double(0.0)
        #     tango.LSX_SetDigJoySpeed(self.LSID, c_xs, c_ys, c_zr, c_zr)

    ## joystickOnOff
    #
    # @param on True/False enable/disable the joystick.
    #
    def joystickOnOff(self, on):
        pass
        # No joystick used

    ## lockout
    #
    # Calls joystickOnOff.
    #
    # @param flag True/False.
    #
    def lockout(self, flag):
        self.joystickOnOff(not flag)

            

    ## setVelocity
    # Not tested yet. I think this should work if we uncomment the last two lines. 
    #
    def setVelocity(self, x_vel, y_vel):
	    # get_velocity_parameters(self)  -> (minimum velocity, acceleration, maximum velocity)
		# set_velocity_parameters(self, min_vel, accn, max_vel):
		xVelocityPars = self.motorX.get_velocity_parameters()
		yVelocityPars = self.motorY.get_velocity_parameters()
		print('current velocity parameters, x-stage, y-stage:')
		print(xVelocityPars)
		print(yVelocityPars)
        # self.motorX(xVelocityPars[0],xVelocityPars[1],x_vel)
		# self.motorY(yVelocityPars[0],yVelocityPars[1],y_vel)

    ## shutDown
    #
    # Disconnect from the stage.
    #
    def shutDown(self):
        # Disconnect from the stage
		pass
		
		
    ## zero
    # Not tested yet.  I think this should work if we uncomment the last line. 
    # Set the current position as the new zero position.
    #
    def zero(self):
        if self.good:
			# not sure we need this. Currently, don't reset anything
			xZero = self.motorX.get_move_home_parameters()[3] # the 4th item is the zero offset
			yZero = self.motorY.get_move_home_parameters()[4] # the 4th item is the zero offset
			print([xZero,yZero])
            # set_move_home_parameters(self, direction, lim_switch, velocity, zero_offset):
