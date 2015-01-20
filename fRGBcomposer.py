#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import os,commands
import pyfits
import numpy as np
from scipy.stats import sigmaclip
from scipy.stats import entropy
import Image
import simplejson

import fitsMaths
import fConfig
import demosaic

class RGBcomposer():

	def __init__(self,RGBdict,gamma=2.2):
		self.Daylight_multipliers={'Ri':2.129439,'Gi1':0.937830,'Gi2':0.937830,'Bi':1.096957,'Gi':0.937830,'P':1.0}
		self.ForwardMatrix1=np.array([[0.7978, 0.1352, 0.0313],[0.2880,0.7119, 0.0001], [0, 0, 0.8251]])
		print self.ForwardMatrix1
		#self.Daylight_multipliers={'Ri':2.500482,'Gi1':1.,'Gi2':1.,'Bi':1.401827,'Gi':1,'u':1.0}
		#self.Daylight_multipliers={'Ri':1.,'Gi1':1.,'Gi2':1.,'Bi':1.,'Gi':1,'P':1.0}
		#RawMeasuredRGGB:125473 256548 256008 160953
		#WB RGGB Levels Daylight         :2153 1024 1024 1594
		#self.Daylight_multipliers={'Ri':2.153,'Gi1':1.024,'Gi2':1.024,'Bi':1.594,'Gi':1.024,'P':1.0}
		self.gamma=gamma
		self.RGBdict=RGBdict
		if len(RGBdict)==1:
			self.luminance()
			self.stiffP()
		else:
			self.rgb()
			self.stiffRGB()

	def setRGBlevels(self):
		bands=self.RGBdict.keys()
		Daylight_multipliers=self.Daylight_multipliers
		maximo=0
		minimo=650000
		for k,B in enumerate(bands):	
			with pyfits.open(self.RGBdict[B]) as hdulist:
				data=hdulist[0].data-hdulist[0].data.min()
				#data=data*Daylight_multipliers[B]
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
				

	def luminance(self,band='P'):
		Daylight_multipliers=self.Daylight_multipliers
		print "RGBcomposer. Luminance fits:",self.RGBdict[band]
		outfile=self.RGBdict[band].replace('fit','tif')
		hdulist=pyfits.open(self.RGBdict[band])
		data=hdulist[0].data-hdulist[0].data.min()
		#data=Daylight_multipliers[band]*data
		if band=='P':
			gammamax=gamma(data,self.gamma).max()
			gammamin=0
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

	def demosaic(self):
		cfaFileName=self.RGBdict['P']
		print "RGBcomposer. Demosaicing:",cfaFileName
		hdulist=pyfits.open(cfaFileName)		
		cfa=hdulist[0].data/hdulist[0].data.max()
		print "CFA Shape:",cfa.shape,cfa.max()
		mosaicStack=demosaic.demosaic(cfa,pattern='rggb',method='bilinear')
		print "Demosaic shape",mosaicStack.shape
		bands=['R','G','B']
		for i,name in enumerate(map(lambda x:'bayer.'+x+'.fit',bands)):
			print "Writing:",name
			hdulist[0].data=mosaicStack[:,:,i]
			print "Band:",hdulist[0].data.max(),hdulist[0].data.min()
			hdulist.writeto(name,clobber=True)

		return mosaicStack

	def toXYZ(self):
		stk=self.demosaic()
		w,h,c=stk.shape
		pixels=w*h
		rgb=stk.reshape(pixels,c)
		print w,h,c,pixels 
		XYZ=np.dot(rgb,self.ForwardMatrix1)
		XYZ=XYZ.reshape(w,h,c)
		print XYZ.shape
		cfaFileName=self.RGBdict['P']
		print "RGBcomposer. XYZ:",cfaFileName
		hdulist=pyfits.open(cfaFileName)
		bands=['X','Y','Z']
		for i,name in enumerate(map(lambda x:'bayer.'+x+'.fit',bands)):
			tifFile=name.replace('.fit','.tif')
			print "Writing:",name
			hdulist[0].data=XYZ[:,:,i]
			hdulist.writeto(name,clobber=True)
			data=lingray(XYZ[:,:,i],a=0.,b=1.,bits=16).astype(np.uint16)
			im = Image.fromarray(data,'I;16')
			Li = im.transpose(Image.FLIP_TOP_BOTTOM)
			print "Generating tif:",tifFile
			Li.save(tifFile,"TIFF")

		if True:
			cmdStr='convert '
			for band in bands:
				cmdStr=cmdStr+'bayer.'+band+'.tif'+' '
			cmdStr=cmdStr+' -set colorspace RGB -combine -set colorspace RGB bayer.XYZ.tiff'
			print cmdStr
			res=commands.getoutput(cmdStr)
			print res

		if True:
			self.stiffXYZ()


	def rgb(self):
		self.setRGBlevels()
		Daylight_multipliers=self.Daylight_multipliers
		outfile="merge.RGB.png"
		bands=self.RGBdict.keys()
		print bands
		im={}
		for k,B in enumerate(['Ri','Gi','Bi']):
			print B
			hdulist=pyfits.open(self.RGBdict[B])
			data=hdulist[0].data-hdulist[0].data.min()
			#data=Daylight_multipliers[B]*data
			data=gamma(data,self.gamma,bits=8)
			data=clip(data)
			data=(lingray(data,a=self.RGBmin,b=self.RGBmax,bits=8)).astype(np.uint8)
			#data=(lingray(data,bits=8)).astype(np.uint8)
			print "Channel: "+B+" 8 Bits,",data.shape,data.dtype		
			print data.min(),data.max(),data.std()
			im[B] = Image.fromarray(data,'L')
			self.luminance(B)
			#im[B].save(outfile+B,"PNG")

		if 'Gi' in self.RGBdict.keys():

			cmdStr='convert '
			for band in ('Ri','Gi','Bi'):
				cmdStr=cmdStr+self.RGBdict[band].replace('fit','tif')+' '
			cmdStr=cmdStr+' -set colorspace RGB -combine -set colorspace sRGB output.RGB.tiff'
			print cmdStr
			res=commands.getoutput(cmdStr)
			print res

			imRGB = Image.merge("RGB", (im['Ri'],im['Gi'], im['Bi']))
			Li = imRGB.transpose(Image.FLIP_TOP_BOTTOM)
			print "Generating png:",outfile
			Li.save(outfile,"PNG")
		else:
			print "Not Gi fits"


	def stiffRGB(self):
		cmdStr='stiff '
		for band in ('Ri','Gi','Bi'):
			cmdStr=cmdStr+self.RGBdict[band]+' '
		cmdStr=cmdStr+'-BITS_PER_CHANNEL 16 -GAMMA '+str(self.gamma)+' -OUTFILE_NAME stiff.RGB.tif'
		print cmdStr
		res=commands.getoutput(cmdStr)
		print res

	def stiffXYZ(self):
		cmdStr='stiff '
		for band in ('X','Y','Z'):
			cmdStr=cmdStr+'bayer.'+band+'.fit'+' '
		cmdStr=cmdStr+'-BITS_PER_CHANNEL 16 -GAMMA '+str(self.gamma)+' -OUTFILE_NAME stiff.XYZ.tif'
		print cmdStr
		res=commands.getoutput(cmdStr)
		print res

	def stiffP(self):
		cmdStr='stiff '
		cmdStr=cmdStr+self.RGBdict['P']+' -BITS_PER_CHANNEL 16 -GAMMA '+str(self.gamma)
		cmdStr=cmdStr+' -OUTFILE_NAME stiff.P.tif'
		print cmdStr
		res=commands.getoutput(cmdStr)
		print res

def clip(array,nsigmas=6):
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
def lingray(x, a=None, b=None,bits=16):
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
	return float(2**bits) * (x-a)/(b-a)



if __name__ == '__main__':
	'''

	'''
	RGBfiles={'Bi': './OUTPUT/result/output.Bi.fit', 'Gi': './OUTPUT/result/output.Gi.fit', 'Ri': './OUTPUT/result/output.Ri.fit'}
	RGBcomposer(RGBfiles,gamma=2.2)
	RGBfiles={'P': './OUTPUT/result/output.P.fit'}
	l=RGBcomposer(RGBfiles,gamma=2.2)
	l.toXYZ()
#	RGBcomposer(RGBfiles,gamma=1)

