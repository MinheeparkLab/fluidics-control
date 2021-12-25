"""
This class is an extendsion of Kilroy for minhee park Lab ORCA setup.

Hyperportocol is a list of protocols, serially executed, each of them are regular kilroy protocol.

To synchronize with Nikon Inverted Microscope we use, Hyperprotocol follows these rules:

 One Image block consists of fluidic part and imaging part. kilroyHyperProtocol receives user input for 
 imaging part duration, automatically generates hyperprotocol.

 During imaging part, kilroy waits until acqusition phase is finished.

 During fluidic part, Nikon waits until fluidics ends.

Code written by : Han, manhyuk (manhyukhan@kaist.ac.kr) 12/23/2021
"""
# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import os
import time
import warnings
import numpy as np
import xml.etree.cElementTree as elementTree
from PyQt5 import QtCore, QtGui, QtWidgets
from kilroyProtocols import KilroyProtocols

__standAlone = False

# ----------------------------------------------------------------------------------------
# Kilroy Class Definition
# ----------------------------------------------------------------------------------------
class KilroyHyperProtocols(QtWidgets.QMainWindow):

    protocol_ready_signal = QtCore.pyqtSignal()
    command_ready_signal = QtCore.pyqtSignal()
    status_change_signal = QtCore.pyqtSignal()
    completed_protocol_signal = QtCore.pyqtSignal(object)
    completed_hyperprotocol_signal = QtCore.pyqtSignal(object)
    change_protocol_signal = QtCore.pyqtSignal()
    
    def __init__(self,
                 hyperprotocol_path = 'protocols',
                 protocol_xml_path = 'default_config.xml',
                 command_xml_path = 'default_config.xml',
                 verbose = False):
        super(KilroyHyperProtocols,self).__init__()

        # Initialize internal attributes
        self.verbose = verbose
        self.hyperprotocol_path = hyperprotocol_path
        self.hyperprotocol_names = list()
        self.hyperprotocol_protocols = list()
        self.hyperprotocol_durations = list()
        self.status = [-1, -1]  # Hyperprotocol ID, protocol ID
        self.num_hyperprotocols = 0
        self.issued_protocol = list()
        # Basis protocol information
        self.protocol_durations = list()
        self.protocol_names = list()
        self.received_message = None
        
        print('----------------------------------------------------------------------')

        self.kilroyProtocols = KilroyProtocols(protocol_xml_path=protocol_xml_path,
                                                command_xml_path=command_xml_path,
                                                verbose = self.verbose)

        self.kilroyProtocols.command_ready_signal.connect(self.transferCommand)
        self.kilroyProtocols.status_change_signal.connect(self.transferStatus)
        self.kilroyProtocols.completed_protocol_signal.connect(self.transferComplete)

        # extract protocol information form kilroyProtocol
        self.protocol_names = self.kilroyProtocols.protocol_names
        self.protocol_durations = [sum(durations) for durations in self.kilroyProtocols.protocol_durations]
        
        if self.verbose:
            print(len(self.protocol_names), len(self.protocol_durations))

        self.createGUI()

        self.loadHyperProtocols(self.hyperprotocol_path)

        self.hyperprotocol_timer = QtCore.QTimer()
        #self.hyperprotocol_timer.setSingleShot(True)
        #self.hyperprotocol_timer.timeout.connect(self.advanceHyperProtocol)

        self.hyper_elapsed_timer = QtCore.QElapsedTimer()
        self.hyper_poll_elapsed_time_timer = QtCore.QTimer()
        self.hyper_poll_elapsed_time_timer.setInterval(1000)
        self.hyper_poll_elapsed_time_timer.timeout.connect(self.updateElapsedTime)
        
    # ----------------------------------------------------------------------------------------
    # Advance the hyperprotocol to the next protocol and issue it
    # ----------------------------------------------------------------------------------------
    def advanceHyperProtocol(self):
        status = self.status
        hyperprotocol_ID = self.status[0]
        protocol_ID = self.status[1] + 1

        if protocol_ID < len(self.hyperprotocol_protocols[hyperprotocol_ID]):
            protocol_name = self.hyperprotocol_protocols[hyperprotocol_ID][protocol_ID]
            protocol_duration = self.hyperprotocol_durations[hyperprotocol_ID][protocol_ID]
            self.status = [hyperprotocol_ID,protocol_ID]
            #self.hyper_elapsed_timer.start()

            self.hyperprotocolDetailsListWidget.setCurrentRow(protocol_ID)

            self.issueProtocol(protocol_name, protocol_duration)            
        else:
            self.stopHyperProtocol()

    # ----------------------------------------------------------------------------------------
    # Close
    # ----------------------------------------------------------------------------------------
    def close(self):
        self.stopHyperProtocol()
        if self.verbose: print("Closing hyperprotocol")
        self.kilroyProtocols.close()

    # ----------------------------------------------------------------------------------------
    # Create display and control widgets
    # ----------------------------------------------------------------------------------------
    def createGUI(self):

        self.mainWidget = QtWidgets.QGroupBox()
        self.mainWidget.setTitle("Hyperprotocols")
        self.mainWidgetLayout = QtWidgets.QGridLayout(self.mainWidget)

        self.leftWidget = QtWidgets.QGroupBox()
        self.leftWidgetLayout = QtWidgets.QVBoxLayout(self.leftWidget)
        self.rightWidget = QtWidgets.QGroupBox()
        self.rightWidgetLayout = QtWidgets.QVBoxLayout(self.rightWidget)

        self.fileLabel = QtWidgets.QLabel()
        self.fileLabel.setText("")

        self.hyperprotocolListWidget = QtWidgets.QListWidget()
        self.hyperprotocolListWidget.currentItemChanged.connect(self.updateHyperProtocolDescriptor)

        self.hyperprotocolDetailsListWidget = QtWidgets.QListWidget()
        
        self.elapsedTimeLabel = QtWidgets.QLabel()
        self.elapsedTimeLabel.setText("Hyperprotocol Elapsed Time: ")

        self.hybeListLabel = QtWidgets.QLabel()
        self.hybeListLabel.setText("list your hybes : ")
        self.ignoreHybeListLabel = QtWidgets.QLabel()
        self.ignoreHybeListLabel.setText("ignore hybes : ")
        self.hyperprotocolNameLabel = QtWidgets.QLabel()
        self.hyperprotocolNameLabel.setText("Name of hyperprotocol : ")
        self.imagingTimeLabel = QtWidgets.QLabel()
        self.imagingTimeLabel.setText("Imaging Duration : ")

        self.hybeList = QtWidgets.QLineEdit()
        self.hybeList.textChanged.connect(self.updateHybeList)        
        self.ignoreHybeList = QtWidgets.QLineEdit()
        self.ignoreHybeList.textChanged.connect(self.updateHybeList)
        self.hyperprotocolName = QtWidgets.QLineEdit()
        self.hyperprotocolName.textChanged.connect(self.updateHyperProtocolName)
        self.imagingTime = QtWidgets.QLineEdit()
        self.imagingTime.textChanged.connect(self.updateImagingTime)

        self.generateHyperProtocolButton = QtWidgets.QPushButton("Generate HyperProtocol")
        self.generateHyperProtocolButton.clicked.connect(self.generateHyperProtocol)
        self.startHyperProtocolButton = QtWidgets.QPushButton("Start HyperProtocol")
        self.startHyperProtocolButton.clicked.connect(self.startHyperProtocolLocally)
        self.stopHyperProtocolButton = QtWidgets.QPushButton("Stop HyperProtocol")
        self.stopHyperProtocolButton.clicked.connect(self.stopHyperProtocol)

        self.mainWidgetLayout.addWidget(self.leftWidget, 0, 0, 1, 2)
        self.mainWidgetLayout.addWidget(self.rightWidget, 0, 2, 1, 2)
        self.leftWidgetLayout.addWidget(self.elapsedTimeLabel)
        self.leftWidgetLayout.addWidget(self.fileLabel)
        self.leftWidgetLayout.addWidget(self.hyperprotocolListWidget)
        self.leftWidgetLayout.addWidget(self.hyperprotocolDetailsListWidget)
        self.rightWidgetLayout.addWidget(self.hybeListLabel)
        self.rightWidgetLayout.addWidget(self.hybeList)
        self.rightWidgetLayout.addWidget(self.ignoreHybeListLabel)
        self.rightWidgetLayout.addWidget(self.ignoreHybeList)
        self.rightWidgetLayout.addWidget(self.imagingTimeLabel)
        self.rightWidgetLayout.addWidget(self.imagingTime)
        self.rightWidgetLayout.addWidget(self.hyperprotocolNameLabel)
        self.rightWidgetLayout.addWidget(self.hyperprotocolName)
        self.rightWidgetLayout.addWidget(self.generateHyperProtocolButton)
        self.rightWidgetLayout.addWidget(self.startHyperProtocolButton)
        self.rightWidgetLayout.addWidget(self.stopHyperProtocolButton)

        # Configure menu items
        self.load_hyperprotocol_action = QtWidgets.QAction("Load HyperProtocol", self)
        self.load_hyperprotocol_action.triggered.connect(self.loadHyperProtocols)

        self.menu_names = self.kilroyProtocols.menu_names
        self.menu_items = self.kilroyProtocols.menu_items

        # Disable buttons
        self.stopHyperProtocolButton.setEnabled(False)

    # ----------------------------------------------------------------------------------------
    # generate hyperprotocol
    # ----------------------------------------------------------------------------------------
    def generateHyperProtocol(self):
        """
        generate hyperprotocol by using hybelist, self.imagingDuration and hyperprotocol_xml_path

        save hyperprotocol as hyperprotocol_xml_path

        updateHyperProtocolDescriptor
        """
        name = self.hyperprotocol_xml_path.split('protocols/')[1].split('.xml')[0]
        xml_tree = elementTree.Element('kilroy_configuration',
                                             num_valves='1',
                                             cnc='True',
                                             num_pumps='1')
        
        kilroy_hyperprotocols = elementTree.Element('kilroy_hyperprotocols')
        kilroy_hyperprotocol = elementTree.Element('hyperprotocol', name=name)

        new_protocols = list()
        new_durations = list()
        for hybe in self.hybelist:
            hybename = 'Hybridize ' + str(hybe)
            new_protocols.append(hybename)
            try:
                new_durations.append(self.protocol_durations[self.protocol_names.index(hybename)])
            except ValueError:
                warnings.warn('Not Valid protocol')
                return
            protocol = elementTree.SubElement(kilroy_hyperprotocol,'protocol',{'name':hybename})
            
            imagingDuration = str(self.imagingDuration).rjust(4,'0')
            thou, hund, tens, ones = imagingDuration[:-3], imagingDuration[-3], imagingDuration[-2], imagingDuration[-1]
            
            def __appendWait(count, deci):
                for i in range(int(count)):
                    elementTree.SubElement(kilroy_hyperprotocol,'protocol',{'name':'Wait Microscopy ' + str(deci)})
                    new_protocols.append(f"Wait Microscopy {deci}")
                    new_durations.append(deci)
            
            __appendWait(thou,1000)
            __appendWait(hund,100)
            __appendWait(tens,10)
            __appendWait(ones,1)

        def _indent(elem, level=0):
            i = '\n\n' + level*"  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    _indent(elem,level+1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i

        kilroy_hyperprotocols.append(kilroy_hyperprotocol)
        xml_tree.append(kilroy_hyperprotocols)
        _indent(xml_tree)
        
        if os.path.isfile(self.hyperprotocol_xml_path):
            warnings.warn('Override exist hyperprotocol')
            os.remove(self.hyperprotocol_xml_path)

        elementTree.ElementTree(xml_tree).write(self.hyperprotocol_xml_path)

        self.hyperprotocol_names.append(name)
        self.hyperprotocol_protocols.append(new_protocols)
        self.hyperprotocol_durations.append(new_durations)
        self.updateGUI()

        #self.loadHyperProtocols(self.hyperprotocol_xml_path)
        
    def getCurrentProtocol(self):
        return self.issued_protocol

    def getNumHyperProtocol(self):
        return self.num_hyperprotocols
    
    def getStatus(self):
        return self.status

    def getHyperProtocolNames(self):
        return self.hyperprotocol_names

    def handleProtocolComplete(self):
        pass

    # ----------------------------------------------------------------------------------------
    # Issue a protocol: load current protocol, send protol ready sig
    # ----------------------------------------------------------------------------------------
    def issueProtocol(self, protocol_data, protocol_duration = -1):
        if "Wait Microscopy" in protocol_data:
            self.issued_protocol = protocol_data
        elif "Hybridize" in protocol_data:
            self.issued_protocol = protocol_data
        else:
            print("not valid protocol")
            return
        
        if self.verbose:
            text = "Issued protocol : " + self.issued_protocol
            if protocol_duration > 0:
                text += ": " + str(protocol_duration) + " s"
            print(text)
         
        if protocol_duration >= 0:
            self.hyperprotocol_timer.start(protocol_duration*1000)

        self.kilroyProtocols.startProtocolByName(protocol_name=self.issued_protocol)

    # ----------------------------------------------------------------------------------------
    # Check to see if hyperprotocol name is in the list of hyperprotocols
    # ----------------------------------------------------------------------------------------
    def isValidHyperProtocol(self, hyperprotocol_name):
        try:
            self.hyperprotocol_names.index(hyperprotocol_name)
            return True
        except ValueError:
            if self.verbose:
                print(hyperprotocol_name + " is not a valid protocol")
            return False

    def isRunningHyperProtocol(self):
        return self.status[0] >= 0
    
    # ----------------------------------------------------------------------------------------
    # Load a protocol xml file
    # ----------------------------------------------------------------------------------------
    def loadHyperProtocols(self, hyperprotocol_path = ''):
        if not hyperprotocol_path:
            hyperprotocol_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "\home")[0]
            if not os.path.isfile(hyperprotocol_path):
                hyperprotocol_path = ''
        
        self.hyperprotocol_xml_path = hyperprotocol_path

        self.parseHyperProtocolXML()

        self.updateGUI()

        if self.verbose:
            self.printHyperProtocols()

    # ----------------------------------------------------------------------------------------
    # Parse loaded xml file: load hyperprotocols
    # ----------------------------------------------------------------------------------------
    def parseHyperProtocolXML(self):
        try:
            print("Parsing for hyperprotocols: " + self.hyperprotocol_xml_path)
            self.xml_tree = elementTree.parse(self.hyperprotocol_xml_path)
            self.kilroy_configuration = self.xml_tree.getroot()
        except:
            print("Valid xml file not loaded")
            return
        
        # Clear previous commands
        self.hyerprotocol_names = list()
        self.hyperprotocol_commands = list()
        self.num_hyperprotocols = 0

        # Load protocols
        for kilroy_hyperprotocols in self.kilroy_configuration.findall('kilroy_hyperprotocols'):

            for hyperprotocol in kilroy_hyperprotocols.findall('hyperprotocol'):
                self.hyerprotocol_names.append(hyperprotocol.get("name"))
                new_protocol_durations= list()
                new_protocol_names = list()

                for protocol in hyperprotocol:
                    name = protocol.get("name")

                    if name in self.protocol_names:
                        new_protocol_names.append(name)
                        new_protocol_durations.append(self.protocol_durations[self.protocol_names.index(name)])
                
                if new_protocol_durations:
                    self.hyperprotocol_durations.append(new_protocol_durations)
                    self.hyperprotocol_protocols.append(new_protocol_names)
            
        self.num_hyperprotocols = len(self.hyperprotocol_names)
        print(len(self.hyperprotocol_names),len(self.hyperprotocol_durations),self.num_hyperprotocols)

    # ----------------------------------------------------------------------------------------
    # Display loaded hyperprotocols
    # ----------------------------------------------------------------------------------------
    def printHyperProtocols(self):
        print("Current hyperprotocols: ")

        for hyperprotocol_ID in range(self.num_hyperprotocols):
            print(self.hyperprotocol_names[hyperprotocol_ID])
            
            for protocol_ID, protocol in enumerate(self.hyperprotocol_protocols[hyperprotocol_ID]):
                textString = "    " + protocol[0] + ": "
                textString += str(self.hyperprotocol_durations[protocol_ID]) + " s"
                print(textString)

    def requiredTime(self, hyperprotocol_name):
        hyperprotocol_ID = self.hyperprotocol_names.index(hyperprotocol_name)
        total_time = 0.0
        for time in self.hyperprotocol_durations[hyperprotocol_ID]:
            total_time += time
        
        return total_time

    # ----------------------------------------------------------------------------------------
    # Initialize and start a hyperprotocol
    # ----------------------------------------------------------------------------------------
    def startHyperProtocol(self):
        hyperprotocol_ID = self.hyperprotocolListWidget.currentRow()

        # Get first protocol in hyperprotocol
        protocol_data = self.hyperprotocol_protocols[hyperprotocol_ID][0]
        protocol_duration = self.hyperprotocol_durations[hyperprotocol_ID][0]

        # Set hyperprotocol status : [hyperprotocol ID, protocol ID]
        self.status = [hyperprotocol_ID, 0]
        self.status_change_signal.emit()

        if self.verbose:
            print("Starting " + self.hyperprotocol_names[hyperprotocol_ID])

        # Start elapsed timer
        self.hyper_elapsed_timer.start()
        self.hyper_poll_elapsed_time_timer.start()

        # Change enable status of GUI items
        self.generateHyperProtocolButton.setEnabled(False)
        self.startHyperProtocolButton.setEnabled(False)
        self.hyperprotocolListWidget.setEnabled(False)
        self.hyperprotocolDetailsListWidget.setCurrentRow(0)
        self.stopHyperProtocolButton.setEnabled(True)

        # Issue
        self.issueProtocol(protocol_data,protocol_duration)
        
        # Start the protocol
        #self.kilroyProtocols.startProtocolByName(protocol_data)

    def startHyperProtocolLocally(self):
        self.startHyperProtocol()
        
    # ----------------------------------------------------------------------------------------
    # Stop a running hyperprotocol either or completion or early
    # ----------------------------------------------------------------------------------------
    def stopHyperProtocol(self):
        # Get name of current hyperprotocol
        if self.status[0] >= 0:
            if self.verbose: print("Stopped Hyperprotocol")
            self.completed_hyperprotocol_signal.emit(self.received_message)

        # Reset status and emit status change signal
        self.status = [-1, -1]
        self.status_change_signal.emit()
        self.received_message = None

        # Stop timer
        self.hyperprotocol_timer.stop()

        # Re-enable GUI
        self.startHyperProtocolButton.setEnabled(True)
        self.generateHyperProtocolButton.setEnabled(True)
        self.hyperprotocolListWidget.setEnabled(True)
        self.stopHyperProtocolButton.setEnabled(False)

        # Unselect all
        self.hyperprotocolDetailsListWidget.setCurrentRow(0)
        try:
            self.hyperprotocolDetailsListWidget.item(0).setSelected(False)
        except:
            print('unselect all failed')

        # Stop timers
        self.hyper_poll_elapsed_time_timer.stop()
        self.elapsedTimeLabel.setText("Hyperprotocol Elapsed Time: ")

    def transferCommand(self):
        self.command_ready_signal.emit()

    def transferComplete(self):
        if self.status[0] < 0:
            self.completed_protocol_signal.emit(None)
        else:
            self.advanceHyperProtocol()
    
    def transferStatus(self):
        # transfer stautus change signal when hyperprotocol not running
        self.status_change_signal.emit()

    def updateElapsedTime(self):
        ms_count = self.hyper_elapsed_timer.elapsed()
        elapsed_seconds = int( float(ms_count) / float(1000))

        text_string = "Hyperprotocol Elapsed Time : "
        text_string += str(elapsed_seconds)
        text_string += " s"
        self.elapsedTimeLabel.setText(text_string)

    def updateGUI(self):
        self.hyperprotocolListWidget.clear()
        
        for name in self.hyperprotocol_names:
            self.hyperprotocolListWidget.addItem(name)

        if len(self.hyperprotocol_names) > 0:
            self.hyperprotocolListWidget.setCurrentRow(0)

        drive, path_and_file = os.path.splitdrive(str(self.hyperprotocol_xml_path))
        path_name, file_name = os.path.split(str(path_and_file))
        self.fileLabel.setText(file_name)
        self.fileLabel.setToolTip(self.hyperprotocol_xml_path)

    def updateHybeList(self):
        """
        update hybe list
        """
        hybestring = self.hybeList.text()
        ignorestring = self.ignoreHybeList.text()

        self.hybelist = hybestring.strip().split()
        self.ignorelist = ignorestring.strip().split()

        try:
            tmp1 = [int(ele) for ele in self.hybelist]
            tmp2 = [int(ele) for ele in self.ignorelist]
        except ValueError:
            try:
                for ind, hybe in enumerate(self.hybelist):
                    st, end = hybe.split('-')[0], hybe.split('-')[-1]
                    if st!=end:
                        e = self.hybelist.pop(ind)
                        assert '-' in e
                        self.hybelist.extend([str(i) for i in range(int(st), int(end) + 1)])

                tmp1 = list(np.int32(self.hybelist))
                for ind, hybe in enumerate(self.ignorelist):
                    st, end = hybe.split('-')[0], hybe.split('-')[-1]
                    if st!=end:
                        e = self.ignorelist.pop(ind)
                        assert '-' in e
                        self.ignorelist.extend([str(i) for i in range(int(st), int(end) + 1)])
                tmp2 = list(np.int32(self.ignorelist))
            except ValueError:
                return

        if len(tmp1) == 1:
            self.hybelist = [i+1 for i in range(tmp1[0])]
        else:
            tmp1 = list(np.unique(tmp1))
            tmp1.sort()
            self.hybelist = tmp1

        self.ignorelist = tmp2
        if len(self.ignorelist) > 0:
            for ignore in self.ignorelist:
                if ignore in self.hybelist: 
                    self.hybelist.remove(ignore)
                else:
                    continue

    def updateHyperProtocolDescriptor(self):
        hyperprotocol_ID = self.hyperprotocolListWidget.currentRow()
        current_hyperprotocol_name = self.hyperprotocol_names[hyperprotocol_ID]
        current_hyperprotocol_protocols = self.hyperprotocol_protocols[hyperprotocol_ID]
        current_hyperprotocol_durations = self.hyperprotocol_durations[hyperprotocol_ID]

        self.hyperprotocolDetailsListWidget.clear()
        
        for ID in range(len(current_hyperprotocol_protocols)):
            text_string = current_hyperprotocol_protocols[ID]
            text_string += ": "
            text_string += str(current_hyperprotocol_durations[ID]) + " s"

            wid = QtWidgets.QListWidgetItem(text_string)
            wid.setFlags(wid.flags() & QtCore.Qt.ItemIsSelectable)
            self.hyperprotocolDetailsListWidget.insertItem(ID, wid)

    def updateHyperProtocolName(self):
        """
        update hyperprotocol name
        """
        self.hyperprotocol_xml_path = 'protocols/' + self.hyperprotocolName.text().strip().split('.xml')[0] + '.xml'

    def updateImagingTime(self):
        """
        update imaging time
        """
        imagingTimeString = self.imagingTime.text()
        try:
            tmp = int(imagingTimeString)
        except ValueError:
            self.imagingDuration = 300
            return
        
        self.imagingDuration = tmp


if __name__ == '__main__':
    __standAlone = True
