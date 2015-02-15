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


	def getSection(self,section=''):
		return dict(self.cfg.items(section))

	def createDirs():
		pass


	def chkConfig(self):
		for section in self.cfg.sections():
			print
			print "================ "+section+" ================"
			for item in self.cfg.items(section):
				print item


if __name__ == '__main__':
	cfg=fConfig()
	cfg.chkConfig()

