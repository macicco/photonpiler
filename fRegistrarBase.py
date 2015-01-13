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

class fBaseComposer():

	def __init__(self,path,dark=True,flat=True):
		self.doDark=dark
		self.doFlat=flat
		self.nsigma=1.5
		#CANON600D bandmap. rawtran do wrong
		self.BandMap={'Ri':'Gi2','Gi1':'Ri','Gi2':'Bi','Bi':'Gi1','u':'u'}
		self.scriptpath, self.scriptname = os.path.split(os.path.abspath(__file__))
		print "Script path:",self.scriptpath
		print "Processing directory:",path
		self.path=path
		self.lightspath=path+"/SCIENCE"
		self.darkspath=path+"/DARKS"
		self.flatspath=path+"/FLATS"
		self.outdir=path+"/OUTPUT"
		self.rawfitsdir=self.outdir+"/rawfits"
		if not os.path.exists(self.outdir):
			os.mkdir(self.outdir) 
		if not os.path.exists(self.rawfitsdir):
			os.mkdir(self.rawfitsdir) 





	def init(self,band):
		dark=self.doDark
		flat=self.doFlat
		print
		print "			============================"
		print "			Processing BAND:",band
		print "			============================"
		print
		self.actualBand=band
		if os.path.exists(self.darkspath) and dark:
			if not os.path.exists(self.outdir+'/masterdark.'+band+'.fit'):
				self.darkRaws=self.searchRawFiles(self.darkspath)
				print
				print "=========== DARK FRAMES ============== BAND:",band
				print "Path:", self.darkspath
				self.darkFits=self.rawtran(self.darkRaws,dark=False,flat=False,rotate=True)
				self.NumDarks=len(self.darkFits)
				print "Darks frames found:",self.NumDarks

				print self.darkRaws
				print self.darkFits
				print
				print "Generating MASTERDARK:",self.outdir+'/masterdark.'+band+'.fit'
				dark=self.MasterDark()
				dark.save(self.outdir+'/masterdark.'+band+'.fit')

			ifile=self.outdir+'/masterdark.'+band+'.fit'

		else:
			print "NO DARKS"
		
		if os.path.exists(self.flatspath) and flat:
			if not os.path.exists(self.outdir+'/masterflat.'+band+'.fit'):
				self.flatRaws=self.searchRawFiles(self.flatspath)
				print
				print "=========== FLAT FRAMES ============== BAND:",band
				print "Path:", self.flatspath
				self.flatFits=self.rawtran(self.flatRaws,dark=True,flat=False,rotate=True)
				self.NumFlats=len(self.flatFits)
				print "Flat frames found:",self.NumFlats
				print self.flatRaws
				print self.flatFits
				print
				print "Generating MASTERFLAT:",self.outdir+'/masterflat.'+band+'.fit'
				flat=self.MasterFlat(op='median')
				flat.save(self.outdir+'/masterflat.'+band+'.fit')

			ifile=self.outdir+'/masterflat.'+band+'.fit'

		else:
			print "NO FLATS"
		print
		print "=========== LIGHT FRAMES ============== BAND:",band
		print "Path:", self.lightspath
		self.lightRaws=self.searchRawFiles(self.lightspath)
		try:
			oldband=self.BaseBand
			self.lightFits=map(lambda x:x.replace(oldband,band),self.lightFitsBase)
			print "Second pass"
			self.rawtran(self.lightRaws,dark,flat)
		except:
			print "First pass"
			self.lightFits=self.rawtran(self.lightRaws,dark,flat)
		print self.lightFits

		self.NumLights=len(self.lightFits)



		print "Light frames found:",self.NumLights
		print self.lightRaws
		print self.lightFits
		print "=========== OUTPUT ============== BAND:",band
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

	def exif2fit(self,raw,fit):
		print "extracting exif information from:",raw
		strCmd= 'exiftool -j '+ raw
		res=commands.getoutput(strCmd)
		exifjson=res.strip().replace('\n','')[1:-1]
		exiftags=simplejson.loads(exifjson)
		print "updating FIT HEADER",fit
		with 	pyfits.open(fit,mode='update') as hdulist:
			header=hdulist[0].header
			header['CCD-TEMP']=float(exiftags['CameraTemperature'].replace(' ','').replace('C',''))
			header['COMMENT']="ORIGINAL EXIF DATA BEGIN:"
			for exifkey in exiftags.keys():
				header['COMMENT']="EXIF:: "+exifkey+":"+str(exiftags[exifkey])
			header['COMMENT']="ORIGINAL EXIF DATA END:"

	def rawtran(self,raws,dark=True,flat=True,rotate=False):
		iband=self.BandMap[self.actualBand]
		band=self.actualBand
		l=[]
		for raw in raws:
			outfile=self.outdir+"/"+os.path.basename(raw).replace('CR2',band+'.fit')
			if not os.path.exists(outfile):
				print ".-.-.-."
				print "rawtran-ting:",outfile
				strCmd= 'rawtran -c '+iband+' -B -32 -o '+outfile+ " " + raw
				print strCmd
				res=commands.getoutput(strCmd)
				print res
				'''Copy exif information to fit'''
				self.exif2fit(raw,outfile)

				rawfits=self.rawfitsdir+"/"+os.path.basename(raw).replace('CR2',band+'.fit')

				print "saving raw fits:",rawfits
				strCmd= 'cp -v '+outfile+ " " + rawfits
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
			print strCmdIMG_6857.Ri.fit
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
		self.rank=np.sort(self.rank,order=['ellipticity','fwhm'],axis=0)
		if k==0:
			print "Only one frame. Not rank"
			self.lightFits=light
			self.lightFitsBase=self.lightFits
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
		self.lightFits=[]
		for s in selected_:
			self.lightFits.append(s)
		print self.lightFits
		self.lightFitsBase=self.lightFits


	def MasterFlat(self,op='median'):
		superflat=self.combine(self.flatFits,op)
		maxi=superflat.hdulist[0].data.mean()
		superflat=(1./maxi)*superflat
		print "Renormalizing mean/std:",superflat.hdulist[0].data.mean(),superflat.hdulist[0].data.std()
		return superflat

	def MasterDark(self,op='median'):
		#return (1./self.NumDarks)*self.Sum(self.darkFits)
		return self.combine(self.darkFits,op)

		

	def Sum(self,fits):
		return self.combine(fits,op='sum')

	def combine(self,fits,combine='median'):
		op_dict={'median':np.median,'mean':np.mean,'max':np.max,'min':np.min,'sum':np.sum}
		for i,fit in enumerate(fits):
			if i==0:
				Master=fitsMaths.fitMaths(fit)
				(xsize,ysize)=Master.hdulist[0].data.shape
				print "Combine:",combine
				print fits
				stackedData=Master.hdulist[0].data.reshape((-1))
				header=Master.hdulist[0].header
				print "FRAME:",i," mean/std:",stackedData.mean(),stackedData.std(),\
				"EXP:",header['EXPTIME'],"ISO:",header['ISO'],"TEMP:",header['CCD-TEMP']

			else:
				frame=fitsMaths.fitMaths(fit)
				frameData=frame.hdulist[0].data.reshape((-1))
				header=Master.hdulist[0].header
				print "FRAME:",i," mean/std:",frameData.mean(),stackedData.std(),\
				"EXP:",header['EXPTIME'],"ISO:",header['ISO'],"TEMP:",header['CCD-TEMP']
				stackedData=np.vstack((stackedData,frameData))
		if i==0:
			print "Combining only 1 frame. Return as its"
			return Master			
		median=op_dict[combine](stackedData,axis=0)
		Master.hdulist[0].data=median.reshape((xsize,ysize))
		print  "combination mean/std",median.mean(),median.std()
		return Master

class RGBcomposer():

	def __init__(self,RGBdict,gamma=2.2):
		#self.Daylight_multipliers={'Ri':2.129439,'Gi1':0.937830,'Gi2':0.937830,'Bi':1.096957,'Gi':0.937830,'u':1.0}
		#self.Daylight_multipliers={'Ri':2.500482,'Gi1':1.,'Gi2':1.,'Bi':1.401827,'Gi':1,'u':1.0}
		#self.Daylight_multipliers={'Ri':1.,'Gi1':1.,'Gi2':1.,'Bi':1.,'Gi':1,'u':1.0}
		#RawMeasuredRGGB:125473 256548 256008 160953
		#WB RGGB Levels Daylight         :2153 1024 1024 1594
		self.Daylight_multipliers={'Ri':2.153,'Gi1':1.024,'Gi2':1.024,'Bi':1.594,'Gi':1.024,'u':1.0}
		self.gamma=gamma
		self.RGBdict=RGBdict
		if len(RGBdict)==1:
			self.luminance()
			self.stiffU()
		else:
			self.rgb()
			self.stiffRGB()

	def getRGBlevels(self):
		bands=self.RGBdict.keys()
		Daylight_multipliers=self.Daylight_multipliers
		maximo=0
		minimo=650000
		for k,B in enumerate(bands):	
			with pyfits.open(self.RGBdict[B]) as hdulist:
				data=hdulist[0].data-hdulist[0].data.min()
				data=data*Daylight_multipliers[B]
				data=gamma(data,self.gamma)
				data=clip(data)
				mi=data.min()
				ma=data.max()
			if maximo<ma:
				maximo=ma
			if minimo>mi:
				minimo=mi
		self.RGBmin=0
		self.RGBmax=maximo-minimo
		print "RGB levels:",self.RGBmin,self.RGBmax
				

	def luminance(self,band='u'):
		Daylight_multipliers=self.Daylight_multipliers
		print "RGBcomposer. Luminance fits:",self.RGBdict[band]
		outfile=self.RGBdict[band].replace('fit','tif')
		hdulist=pyfits.open(self.RGBdict[band])
		data=hdulist[0].data-hdulist[0].data.min()
		data=Daylight_multipliers[band]*data
		if band=='u':
			gammamax=gamma(data,self.gamma,bits=16*3).max()
			gammamin=0
			data=gamma(data,self.gamma,bits=16*3)
		else:
			gammamax=self.RGBmax
			gammamin=self.RGBmin
			data=gamma(data,self.gamma)
		data=clip(data)
		data=lingray(data,a=gammamin,b=gammamax,bits=16).astype(np.uint16)
		#data=lingray(data,bits=16).astype(np.uint16)
		print "luminance: 16 Bits,",data.shape,data.dtype		
		print data.min(),data.max(),data.std()
		im = Image.fromarray(data,'I;16')
		Li = im.transpose(Image.FLIP_TOP_BOTTOM)
		print "Generating tif:",outfile
		Li.save(outfile,"TIFF")

	def rgb(self):
		self.getRGBlevels()
		Daylight_multipliers=self.Daylight_multipliers
		outfile=self.RGBdict['Ri'].replace('Ri.fit','png')
		bands=self.RGBdict.keys()
		print bands
		im={}
		for k,B in enumerate(['Ri','Gi','Bi']):
			print B
			hdulist=pyfits.open(self.RGBdict[B])
			data=hdulist[0].data-hdulist[0].data.min()
			data=Daylight_multipliers[B]*data
			data=gamma(data,self.gamma)
			data=clip(data)
			data=(lingray(data,a=self.RGBmin,b=self.RGBmax,bits=8)).astype(np.uint8)
			#data=(lingray(data,bits=8)).astype(np.uint8)
			print "Channel: "+B+" 8 Bits,",data.shape,data.dtype		
			print data.min(),data.max(),data.std()
			im[B] = Image.fromarray(data,'L')
			self.luminance(B)
			#im[B].save(outfile+B,"PNG")

		if 'Gi' in self.RGBdict.keys():
			imRGB = Image.merge("RGB", (im['Ri'],im['Gi'], im['Bi']))
			cmdStr='convert '
			for band in ('Ri','Gi','Bi'):
				cmdStr=cmdStr+self.RGBdict[band].replace('fit','tif')+' '
			cmdStr=cmdStr+' -set colorspace raw -combine -set colorspace raw output.RGB.tiff'
			print cmdStr
			res=commands.getoutput(cmdStr)
			print res
			Li = imRGB.transpose(Image.FLIP_TOP_BOTTOM)
			print "Generating png:",outfile
			Li.save(outfile,"PNG")
		else:
			print "Not Gi fits"

	def stiffRGB(self):
		cmdStr='stiff '
		for band in ('Ri','Gi','Bi'):
			scaledFits=self.RGBdict[band].replace('fit','scaled.fit')
			with pyfits.open(self.RGBdict[band]) as hdulist:
				hdulist[0].data=self.Daylight_multipliers[band]*hdulist[0].data
				hdulist.writeto(scaledFits,clobber=True) 
			cmdStr=cmdStr+scaledFits+' '
		cmdStr=cmdStr+' -OUTFILE_NAME stiff.RGB.tif'
		print cmdStr
		res=commands.getoutput(cmdStr)
		print res

	def stiffU(self):
		cmdStr='stiff '
		cmdStr=cmdStr+self.RGBdict['u']+' '
		cmdStr=cmdStr+' -OUTFILE_NAME stiff.U.tif'
		print cmdStr
		res=commands.getoutput(cmdStr)
		print res

def clip(array,nsigmas=6):
	'''NOT IMPLEMENTED'''
	return array
	mean=array.mean()
	std=array.std()
	z0=mean-nsigmas*std
	z1=mean+nsigmas*std
	clipped=np.clip(array,z0,z1)
	print "Clip:",z0,z1,mean,std
	if len(clipped)!=len(array):
		print "Clipepd elements ",len(array)-len(clipped),
	else:
		print "Not clip needed"
	return  clipped

def gamma(array,coeff,bits=16):
	maximo=float(2**bits)
	data=array/maximo
	data=data**(1/coeff)
	return maximo*data
	


#Taken from f2n https://svn.epfl.ch/svn/mtewes-public/trunk/f2n/f2n/f2n.py
def lingray(x, a=None, b=None,bits=8):
	"""
	Auxiliary function that specifies the linear gray scale.
	a and b are the cutoffs : if not specified, min and max are used
	"""
	if a == None:
		a = np.min(x)
	if b == None:
		b = np.max(x)
	a=float(a)
	b=float(b)
	return float(2**bits-1) * (x-a)/(b-a)


