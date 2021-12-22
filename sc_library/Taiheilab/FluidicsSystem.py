import sys
import os
import time
from datetime import datetime
import parameters as params_loader
import grblCNC
import gilson_mp3

class FluidicsSystem():
		def __init__(self,
				parameterXML = False):

			self.paramsXML = parameterXML
			self.prms = params_loader.parameters(parameterXML)
			self.devcnc  = grblCNC.G_CNC(self.prms)
			self.devpump = gilson_mp3.APump(self.prms)

			# -- coordinate parameters
			self.coordinatefile = self.prms.get("coordinatefile")
			self.WASHX = self.prms.get("WASHX")
			self.BLEACHX = self.prms.get("BLEACHX")
			self.IMAGINGX = self.prms.get("IMAGINGX")
			self.WASHY = self.prms.get("WASHY")
			self.BLEACHY = self.prms.get("BLEACHY")
			self.IMAGINGY = self.prms.get("IMAGINGY")

			# -- protocol parameters
			self.FLOWSPEED = self.prms.get("FLOWSPEED") # 21 # rpm: 21 rpm is ~500uL/min
			self.FLOWTIME = self.prms.get("FLOWTIME") # 60  # sec
			self.hybtime = self.prms.get("hybtime") # 15*60 # sec
			self.waitingtime_wash = self.prms.get("waitingtime_wash") # 30 # sec
			self.waitingtime_bleach = self.prms.get("waitingtime_bleach") # 1 # sec
			self.waitingtime_imaging = self.prms.get("waitingtime_imaging") # 15*60 # sec
			self.imagingtime = self.prms.get("imagingtime") # 15*60 # sec

		def ORCAProtocolRun(self):
			fcoords = open(self.coordinatefile,'r')
			print('MESSAGE -- Opening coordinate file')
			# create log file
			logfile = './log_'+str(datetime.fromtimestamp(time.time())).split('.')[0].replace(':','-').replace(' ','-')+'.txt' # ex) log_2021-03-06-12-04-38.txt
			f_log = open(logfile,'w')
			f_log.write('ORCAProtocolRun. ParameterFile='+self.paramsXML+'\n')
			f_log.close()
			print('MESSAGE -- Creating log file')
			input('MESSAGE -- Press <Enter> to start.')

			cntr = 1
			for line in fcoords:
				cmd=line.strip().split('\t')
				newx = cmd[0]
				newy = cmd[1]
				logmsg = 'hyb'+str(cntr)+'_'+newx+'_'+newy+'_start--'+str(datetime.fromtimestamp(time.time()))+'\n'
				f_log = open(logfile,'a')
				f_log.write(logmsg)
				f_log.close()
				print(logmsg)
				# ---- sequential flow protocol ---- #
				# format: self.Protocol(CNC_class,Pump_class,X_position,Y_position,WaitingtimeAfterFlowStops,HowLongYouWantToFlow)
				# Protocol method executes 
				#    1. up the needle
				#    2. move to the position as you set in X_position and Y_position
				#    3. down the needle, flow the reagent as you set in FLOWSPEED and FLOWTIME
				#    4. stop the flow, hold for a while as you set in WaitingtimeAfterFlowStops
				# ------------------------------------
				# -- 96 well
				self.Protocol(newx,newy,self.hybtime,self.FLOWTIME)
				# -- wash buffer
				self.Protocol(self.WASHX,self.WASHY,self.waitingtime_wash,self.FLOWTIME*2)
				# -- bleach buffer
				self.Protocol(self.BLEACHX,self.BLEACHY,self.waitingtime_bleach,self.FLOWTIME)
				# -- imaging buffer + hold untile the image aquisition is done
				self.Protocol(self.IMAGINGX,self.IMAGINGY,self.waitingtime_imaging,self.FLOWTIME)
				# ------------------------------------
				# -- write a log
				logmsg = 'hyb'+str(cntr)+'_'+newx+'_'+newy+'_end--'+str(datetime.fromtimestamp(time.time()))+'\n'
				f_log = open(logfile,'a')
				f_log.write(logmsg)
				f_log.close()
				print(logmsg)
				# -- hold for a while until image aquisition is done
				self.Hold(self.imagingtime)
				# ------------------------------------

				cntr = cntr + 1
			print('MESSAGE -- ORCA Protocol is done.')
			fcoords.close()

		def ConstantFlow(self,speed):
			self.devcnc.moveXY('X0','Y0')
			input('press <Enter> to start wash.')
			self.devcnc.needleDown()
			self.devcnc.wait(0.5) # -- command below here are not sent until waiting time ends
			print('start flow')
			self.devpump.startFlow(speed)
			input('press <Enter> to stop wash.')
			print('stop flow')
			self.devpump.stopFlow()
			self.devcnc.needleUp()

		def stageForward(self):
			if self.devcnc.zpos != 'Z0':
				self.devcnc.needleUp()
			self.devcnc.moveXY(fs.devcnc.xpos,'Y150')

		def goHome(self):
			if self.devcnc.zpos != 'Z0':
				self.devcnc.needleUp()
			self.devcnc.moveXY('X0','Y0')

		def Protocol(self,newx,newy,waitingtime,FLOWTIME):
			self.devcnc.needleUp()
			self.devcnc.moveXY(newx,newy)
			self.devcnc.needleDown()
			self.devcnc.wait(1.0) # -- command below here are not sent until waiting time ends
			print('start flow')
			self.devpump.startFlow(self.FLOWSPEED)
			time.sleep(FLOWTIME)
			print('stop flow')
			self.devpump.stopFlow()
			time.sleep(waitingtime)

		def Hold(self,waitingtime):
			self.devcnc.wait(waitingtime) 

# devcnc.serial.close()
# devpump.serial.close()


