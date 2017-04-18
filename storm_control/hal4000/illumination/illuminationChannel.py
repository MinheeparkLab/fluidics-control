#!/usr/bin/env python
"""
This controls a single channel.

Hazen 04/17
"""

import numpy

from PyQt5 import QtCore

import storm_control.sc_hardware.baseClasses.daqModule as daqModule
import storm_control.hal4000.illumination.illuminationChannelUI as illuminationChannelUI


class Channel(QtCore.QObject):
    """
    This class is responsible for orchestrating the behaviour of a
    a single channel.
    """
    functionality_names = ["amplitude_modulation", "analog_modulation", "digital_modulation", "mechanical_shutter"]
    
    def __init__(self, channel_id = 0, configuration = None, **kwds):
        super().__init__(**kwds)

        self.amplitude_range = 1.0
        self.channel_id = channel_id
        self.channel_ui = False
        self.display_normalized = False
        self.filming = False
        self.filming_disabled = False
        self.max_amplitude = 1.0
        self.max_voltage = 1.0
        self.min_amplitude = 0.0
        self.min_voltage = 0.0
        self.name = configuration.get("gui_name")
        self.parameters = False
        self.used_for_film = False
        self.was_on = False
        self.bad_module = True

        #
        # Create variables for communication with the various hardware functionalities.
        #
        # This will add the attributes in the list to this class. Initially these
        # are just the StormXMLObjects describing each functionality that we'll
        # need. During 'configure1' illumination.illumination will request these
        # functionalities. If they are returned the attributes are changed to be
        # the functionalities.
        #
        # amplitude_modulation - A device like a filter wheel or AOTF.
        # analog_modulation - A daq analog out (with hardware timing).
        # digital_modulation - A daq digital out (with hardware timing).
        # mechanical_shutter - Usually a daq digital out connected to shutter that
        #                      backs up an AOTF or filter wheel.
        #
        for name in self.functionality_names:
            if configuration.has(name):
                setattr(self, name, configuration.get(name))
            else:
                setattr(self, name, None)

        if self.analog_modulation is not None:
            self.max_voltage = self.analog_modulation.get("max_voltage")
            self.min_voltage = self.analog_modulation.get("min_voltage")

        #
        # Configure the UI.
        #
        # If we have amplitude modulation then this is an adjustable channel with slider.
        #
        if self.amplitude_modulation is not None:
            self.display_normalized = self.amplitude_modulation.get("display_normalized", True)
            self.max_amplitude = self.amplitude_modulation.get("max_amplitude")
            self.min_amplitude = self.amplitude_modulation.get("min_amplitude", 0)
            
            self.amplitude_range = float(self.max_amplitude - self.min_amplitude)
            self.channel_ui = illuminationChannelUI.ChannelUIAdjustable(name = self.name,
                                                                        color = configuration.get("color"),
                                                                        minimum = self.min_amplitude,
                                                                        maximum = self.max_amplitude,
                                                                        parent = self.parent())
            self.channel_ui.updatePowerText("NS")

        # Otherwise it is a basic channel with on only a on/off radio button.
        else:
            self.channel_ui = illuminationChannelUI.ChannelUI(name = self.name,
                                                              color = configuration.get("color"),
                                                              parent = self.parent())

        self.channel_ui.disableChannel()

    def cleanup(self):
        self.channel_ui.setOnOff(False)
    
    def getAmplitude(self):
        """
        Return the current channel amplitude as a string. This is
        always normalized.
        """
        power = self.channel_ui.getAmplitude()
        return "{0:.4f}".format((power - self.min_amplitude)/self.amplitude_range)

    def getDaqWaveforms(self, waveform, oversampling):
        """
        Return the waveform as a DaqWaveform objects. 
        """
        if self.bad_module:
            return []

        daq_waveforms = []

        # Scale analog waveform.
        if self.analog_modulation is not None:
            temp = waveform * (self.max_voltage - self.min_voltage) - self.min_voltage
            temp = numpy.ascontiguousarray(temp, dtype = numpy.float64)
            daq_waveforms.append(daqModule.DaqWaveform(source = self.analog_modulation.getSource(),
                                                       oversampling = oversampling,
                                                       waveform = temp))

        # Convert waveform to digital.
        if self.digital_modulation is not None:
            temp = numpy.round(numpy.copy(waveform)).astype(numpy.uint8)
            temp[(temp != 0)] = 1
            temp = numpy.ascontiguousarray(temp, dtype = numpy.uint8)
            daq_waveforms.append(daqModule.DaqWaveform(is_analog = False,
                                                       source = self.digital_modulation.getSource(),
                                                       oversampling = oversampling,
                                                       waveform = temp))

        return daq_waveforms
    
    def getFunctionalityNames(self):
        hw_fn_names = []
        for name in self.functionality_names:
            fn = getattr(self, name)
            if fn is not None:
                hw_fn_names.append(fn.get("hw_fn_name"))
        return hw_fn_names
        
    def getName(self):
        return self.name

    def handleOnOffChange(self, on):
        """
        Handles a request to turn the channel on / off. These all
        come from the UI. They are ignored when we are filming.
        
        As a side effect this records the on/off setting in the
        'on_off_state' property of the parameters.
        """
        if self.filming:
            return

        if on:
            if self.amplitude_modulation is not None:
                self.amplitude_modulation.output(self.channel_ui.getAmplitude())
        
            if self.analog_modulation is not None:
                self.analog_modulation.output(self.max_voltage)

        else:
            if self.amplitude_modulation is not None:
                self.amplitude_modulation.output(self.min_amplitude)
        
            if self.analog_modulation is not None:
                self.analog_modulation.output(self.min_voltage)
                
        if self.digital_modulation is not None:
            self.digital_modulation.output(on)

        if self.mechanical_shutter is not None:
            self.mechanical_shutter.output(on)

        self.parameters.get("on_off_state")[self.channel_id] = on

    def handleSetPower(self, new_power):
        """
        Handles requests to set the current channel power to a new value.
        These all come from the UI. The current power is always whatever
        the current value of the slider is.
        
        As a side effect this records the current power setting in
        'default_power' property of the parameters.
        """
        if self.display_normalized:
            power = (new_power - self.min_amplitude)/self.amplitude_range
            power_string = "{0:.4f}".format((new_power - self.min_amplitude)/self.amplitude_range)
        else:
            power = new_power
            power_string = "{0:d}".format(new_power)
        self.parameters.get("default_power")[self.channel_id] = power
        self.channel_ui.updatePowerText(power_string)

        if self.amplitude_modulation is not None:
            self.amplitude_modulation.output(new_power)

        if (self.channel_ui.isOn()):
            if self.mechanical_shutter is not None:
                if (new_power == self.min_amplitude):
                    self.mechanical_shutter.output(False)
                else:
                    self.mechanical_shutter.output(True)

    def newParameters(self, parameters):
        self.parameters = parameters

        # Calculate new power in slider units if necessary.
        new_power = parameters.get("default_power")[self.channel_id]
        if self.display_normalized:
            new_power = int(round(new_power * self.amplitude_range + self.min_amplitude))

        # Update channel settings.
        self.channel_ui.newSettings(parameters.get("on_off_state")[self.channel_id],
                                    new_power)

        # Update buttons.
        self.channel_ui.setupButtons(parameters.get("power_buttons")[self.channel_id])

    def remoteIncPower(self, power_inc):
        """
        Handles power increment requests that come from outside of the illumination UI.
        This is "bounced" off the UI slider, for range checking.
        """
        self.channel_ui.remoteIncPower(int(round(power_inc * self.amplitude_range)))

    def remoteSetPower(self, new_power):
        """
        Handles power requests that come from outside of the illumination UI.
        This is "bounced" off the UI slider, for range checking.
        """
        self.channel_ui.remoteSetPower(int(round(new_power * self.amplitude_range + self.min_amplitude)))
                  
    def setFunctionality(self, fn_name, functionality):
        
        # This both adds the functionality and checks whether we have all
        # the functionalities that we requested.
        all_good = True
        for name in self.functionality_names:
            fn = getattr(self, name)
            if fn is not None:
                if (fn.get("hw_fn_name") == fn_name):
                    setattr(self, name, functionality)
                if not isinstance(getattr(self, name), daqModule.DaqFunctionality):
                    all_good = False

        if all_good:
            self.bad_module = False
            self.channel_ui.enableChannel()
            self.channel_ui.onOffChange.connect(self.handleOnOffChange)
            self.channel_ui.powerChange.connect(self.handleSetPower)
        
    def setUsedForFilm(self, waveform):
        """
        Figure out whether or not this channel is used during filming based
        on the waveform.
        """
        self.used_for_film = False
        if (numpy.count_nonzero(waveform) > 0):
            self.used_for_film = True

    def startFilm(self):
        """
        Called at the start of filming.
        """
        if not self.bad_module:
            
            # Record state to restore after movie
            self.was_on = self.channel_ui.isOn() 

            if self.used_for_film:
                self.channel_ui.enableChannel()

                #
                # Check the radio box without actually turning anything on/off
                # that is not already on/off. Analog and digital modulation are
                # taken over by the daq so we don't need to do anything with
                # them. All we need to do is set the power and open the shutter?
                #
                self.channel_ui.onOffChange.disconnect(self.handleOnOffChange)
                self.channel_ui.setOnOff(True)
                
                if self.amplitude_modulation is not None:
                    self.amplitude_modulation.output(self.channel_ui.getAmplitude())

                if self.mechanical_shutter is not None:                    
                    self.mechanical_shutter.output(True)

                self.channel_ui.startFilm()
            else:
                # Turn off unused channels.
                self.channel_ui.setOnOff(False)
                self.channel_ui.disableChannel()
                self.filming_disabled = True
                
        self.filming = True
    
    def stopFilm(self):
        """
        Called at the end of filming to reset things.
        """
        self.filming = False
        
        if self.filming_disabled:
            self.channel_ui.enableChannel(self.was_on)
            self.filming_disabled = False
        else:
            self.channel_ui.stopFilm()

            # This should restore the pre-film state (open/closed).
            self.channel_ui.onOffChange.connect(self.handleOnOffChange)
            
        self.channel_ui.setOnOff(self.was_on)

#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
