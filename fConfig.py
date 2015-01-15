#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import ConfigParser
import commands,os,sys

class fConfig():
	def __init__(self):
		#General paths
		binpath=os.path.realpath(sys.argv[0])
		configpath=os.path.dirname(binpath)
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.read(configpath+"/photonpiler.cfg")
		self.bands=['Ri','Gi1','Gi2','Bi','P']
		self.BandMap={'Ri':'Gi2','Gi1':'Ri','Gi2':'Bi','Bi':'Gi1','P':'P'}

	def getSection(self,section=''):
		return dict(self.cfg.items(section))

	def createDirs():

		if not os.path.exists(self.general['base_dir']):
			os.makedirs(self.general['base_dir'])	

		if not os.path.isfile(self.general['base_dir']+'/index.html'):
			cmd="cp -av "+configpath+"/html/index.html "+self.general['base_dir']
			res=commands.getoutput(cmd)
			print res


	def chkConfig(self):
		for section in self.cfg.sections():
			print
			print "================ "+section+" ================"
			for item in self.cfg.items(section):
				print item

if __name__ == '__main__':
	cfg=fConfig()
	cfg.chkConfig()

