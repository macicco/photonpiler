#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import ConfigParser

class fConfig():
	def __init__(self):
		#General paths
		binpath=os.path.realpath(sys.argv[0])
		configpath=os.path.dirname(binpath)
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.read(configpath+"/photonpiler.cfg")
		self.chkConfig()
		self.general=dict(self.cfg.items('RAW'))
		if not os.path.exists(self.general['base_dir']):
			os.makedirs(self.general['base_dir'])	
			os.makedirs(self.general['base_dir']+'/tmp')
			os.makedirs(self.general['log_dir'])
		if not os.path.isfile(self.general['base_dir']+'/index.html'):
			cmd="cp -av "+configpath+"/html/index.html "+self.general['base_dir']
			res=commands.getoutput(cmd)
			print res
		if not os.path.isfile(self.general['base_dir']+'/style.css'):
			cmd="cp -av "+configpath+"/html/style.css "+self.general['base_dir']
			res=commands.getoutput(cmd)
			print res
		if not os.path.exists(self.general['base_dir']+'/test'):
			cmd="cp -av "+configpath+"/test "+self.general['base_dir']
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

