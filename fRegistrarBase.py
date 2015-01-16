#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import fitsMaths
import os,commands
import pyfits
import numpy as np
from scipy.stats import sigmaclip
from scipy.stats import entropy
import Image
import simplejson
import fConfig

class registrarBase():
	'''
	Base registrar class. Searhc files, sex and rank
	'''
	def __init__(self):
		config=fConfig.fConfig()
		cfg=config.getSection('REGISTRAR')
		self.cfg=cfg
		self.bands=config.bands
		self.BandMap=config.BandMap
		self.scriptpath, self.scriptname = os.path.split(os.path.abspath(__file__))
		print "Script path:",self.scriptpath
		lightFits=self.searchDirs()
		self.fitFrames={'lightsBase':lightFits}
		self.num={'lightsBase':len(lightFits)}
		self.nsigma=1.4
		self.rankdt=np.dtype([('frame',int),('framename',object),('rank',int),\
				('register',bool),('fwhm',float),('ellipticity',float)])


	def searchDirs(self):
		cfg=self.cfg
		lightFits={}
		for B in self.bands:
			path=cfg['fitsdir']+'/'+B+'/'+cfg['lightsdir']
			lightFits[B]=self.searchFitFiles(path)
		return lightFits

	def searchFitFiles(self,path):
		l=[]
		if  os.path.exists(path):
			for file in os.listdir(path):
			    if file.endswith(".fit"):
				l.append(path+"/"+file)
		else:
			print "Path do not exist:",path
		return l

	def fitStats(self,fit):
		with pyfits.open(fit) as hdulist:
			header=hdulist[0].header
			ISO=header['ISO']
			exp=header['EXPTIME']
			Temp=header['CCD-TEMP']
			mean=hdulist[0].mean()
			maxi=hdulist[0].max()
			mini=hdulist[0].min()
			std=hdulist[0].std()	
			print ISO,exp,Temp,mini,maxi,mean,std

	def sex(self,fit,extra=''):
		name=fit.replace('.fit','.cat')
		if not os.path.exists(name):
			#outfile=self.outdir+"/"+os.path.basename(fit).replace('fit','cat')
			sexStr="sex "+fit+" -c "+self.scriptpath+"/registra.sex -CATALOG_NAME "+name+ \
			" -PARAMETERS_NAME "+self.scriptpath+"/registra.param"+ \
			" -FILTER_NAME "+self.scriptpath+"/registra.conv " +extra
			print "EXECUTING:",sexStr
			res=commands.getoutput(sexStr)
			print res

		hdulist=pyfits.open(name)
		data=hdulist[1].data
		return data

	def getQuality(self,data):
		fwhm=data['FWHM_IMAGE']
		ellipticity=data['ELLIPTICITY']
		print fwhm.mean(),ellipticity.mean()
		fwhm_filter,xlow,xhigh=sigmaclip(fwhm,low=self.nsigma,high=self.nsigma)
		ellipticity_filter,xlow,xhigh=sigmaclip(ellipticity,low=self.nsigma,high=self.nsigma)
		meanFWHM,meanELLIPTICITY=fwhm_filter.mean(),ellipticity_filter.mean()
		return meanFWHM,meanELLIPTICITY


	def filterSources(self,n,maxFWHM):
		data=self.sex(n)
		flt=((data['FWHM_IMAGE']<=maxFWHM))
		filter_data=data[flt]
		return filter_data

	def rankFrames(self,band):
		self.rank=np.zeros((1,),dtype=self.rankdt)
		for k,light in enumerate(self.fitFrames['lightsBase'][band]):
			print "Extracting sources and rank:",light
			data=self.sex(light)
			meanFWHM,meanELLIPTICITY=self.getQuality(data)
			print meanFWHM,meanELLIPTICITY
			rank=np.zeros((1,),dtype=self.rankdt)
			if len(self.rank)==1 and self.rank['fwhm']==0:
				self.rank['frame']=k
				self.rank['framename']=light
				self.rank['fwhm']=meanFWHM
				self.rank['ellipticity']=meanELLIPTICITY
			else:
				rank['frame']=k
				rank['framename']=light
				rank['fwhm']=meanFWHM
				rank['ellipticity']=meanELLIPTICITY
				self.rank=np.vstack((self.rank,rank))
		self.rank=np.sort(self.rank,order=['ellipticity','fwhm'],axis=0)
		if k==0:
			print "Only one frame. Not rank"
			for B in self.bands:
				self.fitFrames['lights'][B]=self.fitFrames['lightsBase'][band][0]
			return
		print "Sorting"

		#sigmaclip
		fwhm_filter,xlow,xhigh=sigmaclip(self.rank['fwhm'],low=self.nsigma,high=self.nsigma)
		maxfwhm=fwhm_filter.mean()+fwhm_filter.std()*self.nsigma
		flt=(self.rank['fwhm']<=maxfwhm )
		selected=self.rank[flt]
		ellipticity_filter,xlow,xhigh=sigmaclip(self.rank['ellipticity'],low=self.nsigma,high=self.nsigma)
		maxEllip=ellipticity_filter.mean()+ellipticity_filter.std()*self.nsigma
		flt=(selected['ellipticity']<=maxEllip )
		selected=selected[flt]
		print self.rank
		print maxEllip
		print selected
		selected_=selected['framename']
		dummy=[]
		for s in selected_:
			dummy.append(s)
		self.fitFrames['lights']=dummy





