"""
This class generates a Kilroy protocol for given Nikon ND Acquisition setting.

Code written by : Han, manhyuk (manhyukhan@kaist.ac.kr) 12/22/2021

kilroy protocol format : xml
<?xml version="1.0" encoding="ISO-8859-1"?>

<kilroy_configuration>
    <kilroy_protocols>
        <protocol name = str name>
        <pump ...
        <valve ...
        </protocol>

    </kilroy_protocols>
</kilroy configuration>

"""
import os
import sys
import xml.etree.ElementTree as elementTree
import warnings
from kilroy import Kilroy

__version__ = "1.1.0"

class genProtocol():

    setHybTime = 20
    washBufferTime = 20
    imagingBufferTime = 20
    blechBufferTime = 20
    timeBuffer = 10
    
    def __init__(self,
                 num_hybes = 10,
                 hybelist = None):

        self.default = "default_config.xml"
        self.num_hybes = num_hybes
        if hybelist is None:
            warnings.warn('hybelist is not provided. Automatically set 1 to last')
            self.hybelist = [i+1 for i in range(self.num_hybes)]
        else: self.hybelist = hybelist

        try:
            self.defaultConfig = elementTree.parse(self.default)
            self.kilroy_configuration = self.defaultConfig.getroot()
        except:
            raise FileNotFoundError("Can't find Default configuration file")
        
        self.protocols = dict()
        self.protocol_names = list()
        self.protocol_commands = list()
        self.protocol_durations = list()
        self.num_protocols = 0

        for kilroy_protocols in self.kilroy_configuration.findall("kilroy_protocols"):
            protocol_list = kilroy_protocols.findall("protocol")
            for protocol in protocol_list:
                self.protocol_names.append(protocol.get("name"))
                new_protocol_commands = []
                new_protocol_durations = []
                for command in protocol: # Get all children
                    new_protocol_durations.append(int(command.get("duration")))
                    new_protocol_commands.append([command.tag,command.text]) # [Instrument Type, Command Name]
                    if (not (command.tag == "pump")) and (not (command.tag == "valve")):
                        print("Unknown command tag: " + command.tag)
                self.protocol_commands.append(new_protocol_commands)
                self.protocol_durations.append(new_protocol_durations)

        self.num_protocols = len(self.protocol_names)

        for ind, name in enumerate(self.protocol_names):
            self.protocols[name] = (self.protocol_commands[ind],self.protocol_durations[ind])

    def generateXML(self,name = 'new_protocol.xml', imagingtime = 0):
        assert type(imagingtime) == int
        print(f"MESSAGE -- duration for your imaging is {imagingtime} sec")

        if imagingtime == 0:
            warnings.warn('WARNING -- duration for you imaging time is zero.')

        if not os.path.isdir(os.getcwd()+'/protocols'):
            os.mkdir('protocols')
        
        name = "protocols/" + name

        if os.path.isfile(name):
            os.remove(name)
            print(f'MESSAGE -- file {name} already exists. Overrided...')

        assert self.hybelist and len(self.hybelist) == self.num_hybes

        new_protocol_name = name.split("/")[1].split('.xml')[0]
        new_protocol_commands = list()
        new_protocol_durations = list()

        root = self.kilroy_configuration
        kilroy_protocols = elementTree.Element('kilroy_protocols')
        kilroy_protocol = elementTree.Element('protocol',name=f'{new_protocol_name}')
        
        for hybe in self.hybelist:
            commands, durations = self.protocols[f'Hybridize {hybe}']
            
            for ind, command in enumerate(commands):
                kilroy_command = elementTree.Element(f'{command[0]}',duration=f'{durations[ind]}')
                kilroy_command.text = command[1]
                kilroy_protocol.append(kilroy_command)
            
            ## buffer for imaging
            buffer = imagingtime
            buffer_command = elementTree.Element('pump', duration = str(buffer))
            buffer_command.text = 'Stop Flow'
            kilroy_protocol.append(buffer_command)

        kilroy_protocols.append(kilroy_protocol)
        root.append(kilroy_protocols)

        self.indent(root)
        elementTree.ElementTree(root).write(name)

    def indent(self,elem, level=0):
        i = '\n\n' + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem,level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def getFluidicTime(self):
        totalTime, maxTime = self.calFluidicTime()
        return totalTime,maxTime    

    def calFluidicTime(self):
        totalTime = list()
        for hybe in self.hybelist:
            commands, durations = self.protocols[f'Hybridize {hybe}']
            
            time = 0
            for ind,command in enumerate(commands):
                if command[0] == 'pump': time += durations[ind]
                else:
                    time += self.timeBuffer
                    if command[1] == 'Imaging Buffer' : time += self.imagingBufferTime
                    elif command[1] == 'Wash Buffer' : time += self.washBufferTime
                    elif command[1] == 'Bleach Buffer' : time += self.blechBufferTime
            totalTime.append(time)
        return sum(totalTime),max(totalTime)

if __name__ == '__main__':

    print(f"MESSAGE -- XML generator ver {__version__}")
    
    num_hybes = input("MESSGAE -- the number of hybes (default 10) :     ")
    if len(num_hybes) == 0: num_hybes = 10

    hybelist = input("MESSAGE -- list of hybes (e.g. 4 5 6 10) defualt 1 to given number of hybes :     ")

    if hybelist == '': hybelist = None
    else: hybelist = hybelist.split()

    name = input('MESSAGE -- protocol file name (e.g. protocol.xml) ...... xml :     ')
    if len(name) == 0: name = 'new_protocol.xml'

    imagingtime = input("MESSAGE -- duration for each imaging step (make sure you flag duration tap!) ...... sec :     ")

    genprotocol = genProtocol(num_hybes=num_hybes, hybelist=hybelist)

    genprotocol.generateXML(name=name,imagingtime=int(imagingtime))

    print(f"\nMESSGAE -- new protocol protocols/{name} is successfully generated!\n")
    print(f"Estimated fluidic time for each step is {genprotocol.getFluidicTime()[1]} sec\n\n\n")


