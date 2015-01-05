#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import fitsMaths
import os,commands
import pyfits
import numpy as np
from scipy.stats import sigmaclip


class fBaseComposer():

	def __init__(self,path):
		self.nsigma=1.5
		self.BandMap={'Ri':'Gi2','Gi1':'Ri','Gi2':'Bi','Bi':'Gi1','u':'u'}
		self.scriptpath, self.scriptname = os.path.split(os.path.abspath(__file__))
		print "Script path:",self.scriptpath
		print "Processing directory:",path
		self.path=path
		self.lightspath=path+"/SCIENCE"
		self.darkspath=path+"/DARKS"
		self.flatspath=path+"/FLATS"
		self.outdir=path+"/OUTPUT"
		if not os.path.exists(self.outdir):
			os.mkdir(self.outdir) 
		self.BaseBand='Gi1'
		self.init(self.BaseBand)

	def init(self,band):
		print "Processing BAND:",band
		self.actualBand=band
		if os.path.exists(self.darkspath):
			if not os.path.exists(self.outdir+'/masterdark.'+band+'.fit'):
				self.darkRaws=self.searchRawFiles(self.darkspath)
				self.darkFits=self.rawtran(self.darkRaws,dark=False,flat=False)
				self.NumDarks=len(self.darkFits)
				dark=self.MasterDark()
				dark.save(self.outdir+'/masterdark.'+band+'.fit')
				print "=========== DARK FRAMES =============="
				print "Path:", self.darkspath
				print "Light frames found:",self.NumDarks
				print self.darkRaws
				print self.darkFits
			ifile=self.outdir+'/masterdark.'+band+'.fit'

		else:
			print "NO DARKS"
		
		if os.path.exists(self.flatspath):
			if not os.path.exists(self.outdir+'/masterflat.'+band+'.fit'):
				self.flatRaws=self.searchRawFiles(self.flatspath)
				self.flatFits=self.rawtran(self.flatRaws,dark=True,flat=False,rotate=True)
				self.NumFlats=len(self.flatFits)
				flat=self.MasterFlat()
				flat.save(self.outdir+'/masterflat.'+band+'.fit')
				print "=========== FLAT FRAMES =============="
				print "Path:", self.flatspath
				print "Light frames found:",self.NumFlats
				print self.flatRaws
				print self.flatFits
			ifile=self.outdir+'/masterflat.'+band+'.fit'

		else:
			print "NO FLATS"


		self.lightRaws=self.searchRawFiles(self.lightspath)
		try:
			oldband=self.BaseBand
			self.lightFits=map(lambda x:x.replace(oldband,band),self.lightFits)
			print "Second pass"
			self.rawtran(self.lightRaws)
		except:
			print "First pass"
			self.lightFits=self.rawtran(self.lightRaws)

		self.NumLights=len(self.lightFits)

		print "=========== LIGHT FRAMES =============="
		print "Path:", self.lightspath
		print "Light frames found:",self.NumLights
		print self.lightRaws
		print self.lightFits
		print "=========== OUTPUT =============="
		print "Path:", self.outdir
		self.rankdt=np.dtype([('frame',int),('framename',object),('rank',int),\
				('register',bool),('fwhm',float),('ellipticity',float)])
		self.rank=np.zeros((1,),dtype=self.rankdt)





	def searchRawFiles(self,path):
		l=[]
		for file in os.listdir(path):
		    if file.endswith(".CR2"):
			l.append(path+"/"+file)
		return l

	def rawtran(self,raws,dark=True,flat=False,rotate=False):
		iband=self.BandMap[self.actualBand]
		band=self.actualBand
		l=[]
		for raw in raws:
			outfile=self.outdir+"/"+os.path.basename(raw).replace('CR2',band+'.fit')
			if not os.path.exists(outfile):
				print "rawtran-ting:",outfile
				strCmd= 'rawtran -c '+iband+' -B -32 -o '+outfile+ " " + raw
				print strCmd
				res=commands.getoutput(strCmd)
				print res
				if rotate:
					light=fitsMaths.fitMaths(outfile)
					light=light.rotate90()
					light.save(outfile)
				if dark:
					darkfile=self.outdir+'/masterdark.'+band+'.fit'
					if os.path.exists(darkfile):
						light=fitsMaths.fitMaths(outfile)
						light=light.dark(darkfile)
						light.save(outfile)

						
				if flat:
					flatfile=self.outdir+'/masterflat.'+band+'.fit'
					if os.path.exists(flatfile):
						light=fitsMaths.fitMaths(outfile)
						light=light.flat(flatfile)
						light.save(outfile)
			else:
				print "Already exist:",outfile
			l.append(outfile)
		return l

	def getRGB(self):
		BandMap=self.BandMap
		fit=self.lightFits[0]
		for B in ['Ri','Gi1','Gi2','Bi']: 
		    raw=self.lightspath+'/'+os.path.basename(fit).replace('.fit','.CR2')
   		    outfile=self.outdir+"/"+os.path.basename(raw).replace('.CR2','.'+B+'.fit')
		    if not os.path.exists(outfile):
			print "rawtran-ting:",outfile
			strCmd= 'rawtran -c '+BandMap[B]+' -B -32 -o '+outfile+ " " + raw
			print strCmd
			res=commands.getoutput(strCmd)
			print res

	def sex(self,n,extra=''):
		fit=self.lightFits[n]	
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

	def rankFrames(self):
		for k,light in enumerate(self.lightFits):
			print "Extracting sources and rank:",light
			data=self.sex(k)
			fit=self.lightFits[k]
			meanFWHM,meanELLIPTICITY=self.getQuality(data)
			print meanFWHM,meanELLIPTICITY
			rank=np.zeros((1,),dtype=self.rankdt)
			if len(self.rank)==1 and self.rank['fwhm']==0:
				self.rank['frame']=k
				self.rank['framename']=fit
				self.rank['fwhm']=meanFWHM
				self.rank['ellipticity']=meanELLIPTICITY
			else:
				rank['frame']=k
				rank['framename']=fit
				rank['fwhm']=meanFWHM
				rank['ellipticity']=meanELLIPTICITY
				self.rank=np.vstack((self.rank,rank))

		print "Sorting"
		self.rank=np.sort(self.rank,order=['ellipticity','fwhm'],axis=0)
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
		self.lightFits=[]
		for s in selected_:
			self.lightFits.append(s)
		print self.lightFits


	def MasterFlat(self):
		superflat=self.Sum(self.flatFits)
		mean=superflat.hdulist[0].data.max()
		return (1./mean)*superflat

	def MasterDark(self):
		return (1./self.NumDarks)*self.Sum(self.darkFits)

		

	def Sum(self,fits):

		for i,fit in enumerate(fits):
			if i==0:
				Master=fitsMaths.fitMaths(fit)
				print "init sum:",fit
			else:
				Master=fitsMaths.fitMaths(fit)+Master
				print "+",fit
		return Master

