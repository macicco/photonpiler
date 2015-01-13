#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import fitsMaths
import fBase
import os,commands
import numpy as np
from scipy.stats import sigmaclip
from scipy.ndimage.interpolation import shift
'''
Astrometric registration
NOT FINISHED!
'''
class registrarAstrometry(fBaseComposer.fBaseComposer):

	def astrometry(self):
		self.solve_fits=map(lambda x:x.replace('.fit','.new'),self.lightFits)
		for i,fit in enumerate(self.lightFits):
			astrometryStr="solve-field  "+fit +" -z 4 --overwrite -p"
			print "EXECUTING:\n",astrometryStr
			res=commands.getoutput(astrometryStr)
			print res


	def catalog(self):
		for light in self.solve_fits:
			self.sex(light)	

	def scamp(self):
		cats=map(lambda x:x.replace('.fit','.cat'),self.lightFits)
		lista=" "
		for i,cat in enumerate(cats):
			lista=lista+" "+cat
		print "SCAMP catalogs:\n",cats
		swarpStr="scamp -c "+self.scriptpath+"/scamp.conf "+lista 
		print "EXECUTING:\n",swarpStr
		res=commands.getoutput(swarpStr)
		print res

	def swarp(self):
		lista=" "
		for i,fit in enumerate(self.lightFits):
			lista=lista+" "+fit
		path=cfg['dir_swarp_base']+'/'+self.getToday()+'/swarp'
		if not os.path.exists( path):
    			os.makedirs(path)
		swarpStr="swarp -c "+cfg["swarpcfg"]+lista+ " -IMAGEOUT_NAME "+path+"/"+self.frame+".fit "+\
		" -WEIGHTOUT_NAME  "+path+"/" +self.frame+".weight.fit "
		print "EXECUTING:\n",swarpStr
		res=commands.getoutput(swarpStr)
		print res
		return path+"/"+self.frame+".fit"

	def match(self):
		seeing=60

		for i,light in enumerate(self.lightFits):
			if i==0:
				cat1=self.lightFits[i].replace('.fit','.cat')				
			else:
				cat2=self.lightFits[i].replace('.fit','.cat')
				stiltsStr="stilts tmatch2  fixcols=none in1="+cat1+ " in2="+cat2+" \
					matcher=sky params="+str(seeing)+" \
			       		values1=\"X_IMAGE Y_IMAGE\" \
       					values2=\"X_IMAGE Y_IMAGE\" \
				   	join=1and1  \
					out="+name+".matched.cat  ofmt=fits-basic"
				print stiltsStr
				res=commands.getoutput(stiltsStr)
				print res


