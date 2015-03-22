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

'''
Class for processing fits channels to obtain color imagen.
The input files could be one of this:
	- Independen R,G,B fits
	- Aligned CFA. 'P' Channel
'''

class ColorMixer():

	def __init__(self,inputDict,gamma=2.2):
		self.Daylight_multipliers={'Ri':2.129439,'Gi1':0.937830,'Gi2':0.937830,'Bi':1.096957,'Gi':0.937830,'P':1.0}
		self.ForwardMatrix1=np.array([[0.7978, 0.1352, 0.0313],[0.2880,0.7119, 0.0001], [0, 0, 0.8251]])
		#print self.ForwardMatrix1
		self.gamma=gamma
		self.setNames(inputDict)


	def setNames(self,inputDict):
		self.inputDict=inputDict
		self.rgbBands=('R','G','B')
		self.xyzBands=('X','Y','Z')
		self.cfaBand=('P')
		if all (k in inputDict for k in self.rgbBands):
			self.rgb=True
			self.rgbInputDict={k: inputDict[k] for k in self.rgbBands}
			dirname=os.path.dirname(inputDict[self.rgbBands[0]])
			self.rgbFits={k: dirname+'/rgb.'+k+'.fit' for k in self.xyzBands}
			for B in self.rgbBands:
				self.rgbFits[B]=inputDict[B]
			print self.rgbBands
			print self.rgbInputDict
			print self.rgbFits

		if self.cfaBand in inputDict:
			self.cfa=True
			self.cfaInputDict={k: inputDict[k] for k in self.cfaBand}
			dirname=os.path.dirname(inputDict[self.cfaBand])
			self.cfaFits={k: dirname+'/cfa.'+k+'.fit' for k in self.rgbBands}
			for B in self.xyzBands:
				self.cfaFits[B]=dirname+'/cfa.'+B+'.fit'
			print self.cfaBand
			print self.cfaInputDict
			print self.cfaFits




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

	def cfa2rgb(self):
		cfaFileName=self.cfaInputDict[self.cfaBand]
		print "ColorComposer. Demosaicing:",cfaFileName
		hdulist=pyfits.open(cfaFileName)		
		cfa=hdulist[0].data/hdulist[0].data.max()
		print "CFA Shape:",cfa.shape,cfa.max()
		mosaicStack=demosaic.demosaic(cfa,pattern='rggb',method='bilinear')
		print "Demosaic shape",mosaicStack.shape
		bands=self.rgbBands
		for i,B in enumerate(bands):
			name=self.cfaFits[B]
			print "Writing:",name
			hdulist[0].data=mosaicStack[:,:,i]
			print "Band:",B,hdulist[0].data.max(),hdulist[0].data.min()
			hdulist.writeto(name,clobber=True)
		return mosaicStack


	def cfa2xyz(self):
		stk=self.cfa2rgb()
		w,h,c=stk.shape
		pixels=w*h
		rgb=stk.reshape(pixels,c)
		print w,h,c,pixels 
		XYZ=np.dot(rgb,self.ForwardMatrix1)
		XYZ=XYZ.reshape(w,h,c)
		print XYZ.shape
		cfaFileName=self.cfaInputDict[self.cfaBand]
		print "ColorComposer. XYZ:",cfaFileName
		hdulist=pyfits.open(cfaFileName)
		bands=self.xyzBands
		for i,B in enumerate(bands):
			name=self.cfaFits[B]	
			print "Writing:",name
			hdulist[0].data=XYZ[:,:,i]
			hdulist.writeto(name,clobber=True)

	def rgb2xyz(self):
		for k,B in enumerate(self.rgbBands):
			hdulist=pyfits.open(self.rgbInputDict[B])
			b=np.array(hdulist[0].data)
			w,h=b.shape
			pixels=w*h
			b=b.reshape(pixels)
			if k==0:
				rgb=b
				print rgb.shape,self.ForwardMatrix1.shape
			else:
				rgb=np.dstack((rgb,b))
				print rgb.shape,self.ForwardMatrix1.shape

		XYZ=np.dot(rgb,self.ForwardMatrix1)
		print "XYZ shape:",XYZ.shape
		XYZ=XYZ.reshape(w,h,3)
		print "XYZ shape:",XYZ.shape
		bands=self.xyzBands
		for i,B in enumerate(bands):
			name=self.rgbFits[B]
			print "Writing:",name
			hdulist[0].data=XYZ[:,:,i]
			hdulist.writeto(name,clobber=True)




	def rgb(self):
		self.setRGBlevels()
		Daylight_multipliers=self.Daylight_multipliers
		outfile="merge.RGB.png"
		bands=self.RGBdict.keys()
		print bands
		im={}
		for k,B in enumerate(['R','G','B']):
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

		if 'G' in self.RGBdict.keys():

			cmdStr='convert '
			for band in ('R','G','B'):
				cmdStr=cmdStr+self.RGBdict[band].replace('fit','tif')+' '
			cmdStr=cmdStr+' -set colorspace RGB -combine -set colorspace sRGB output.RGB.tiff'
			print cmdStr
			res=commands.getoutput(cmdStr)
			print res

			imRGB = Image.merge("RGB", (im['R'],im['G'], im['B']))
			Li = imRGB.transpose(Image.FLIP_TOP_BOTTOM)
			print "Generating png:",outfile
			Li.save(outfile,"PNG")
		else:
			print "Not G fits"

	def tifRGB(self):
		bands=['R','G','B']
		cmdStr='convert '
		for band in bands:
			cmdStr=cmdStr+'stacked.'+band+'.tif'+' '
		cmdStr=cmdStr+' -set colorspace RGB -combine -set colorspace RGB stacked.XYZ.tiff'
		print cmdStr
		res=commands.getoutput(cmdStr)
		print res

	def tifXYZ(self):
		bands=['X','Y','Z']
		cmdStr='convert '
		for band in bands:
			cmdStr=cmdStr+'stacked.'+band+'.tif'+' '
		cmdStr=cmdStr+' -set colorspace RGB -combine -set colorspace RGB stacked.XYZ.tiff'
		print cmdStr
		res=commands.getoutput(cmdStr)
		print res




	def stiff(self,origen,channels,output,bits=16):
		if len(channels)==1:
			print "Stiff: Only one channel. Doing Luminance.",
		elif len(channels)==3:
			print "Stiff: 3 channels.",
		else:
			print "Wrong number of channels. Channels dict:"
			print channels
			return
		print "Origen:",origen
		if origen=='CFA':
			channelFits=self.cfaFits
		elif origen=='RGB':
			channelFits=self.rgbFits
		else:
			print "Stiff: Not origen set"
		cmdStr='stiff '
		for band in channels:
			cmdStr=cmdStr+channelFits[band]+' '
		cmdStr=cmdStr+'-BITS_PER_CHANNEL '+str(bits)+' -GAMMA '+str(self.gamma)+' -OUTFILE_NAME '+output+" -c default.stiff"
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
	config=fConfig.fConfig()
	cfg=config.getSection('COLORMIXER')
	gamma=float(cfg['gamma'])
	bits=float(cfg['bits'])
	if int(cfg['do_cfa_process'])==1:
		fits={'B': './OUTPUT/result/stacked.B.fit', 'G': './OUTPUT/result/stacked.G.fit', 'R': './OUTPUT/result/stacked.R.fit','P': './OUTPUT/result/stacked.P.fit'}
		l=ColorMixer(fits,gamma=gamma)
		l.cfa2xyz()
		l.rgb2xyz()
		l.stiff('CFA',l.rgbBands,'cfa.cfa.RGB.tif',bits=bits)
		l.stiff('RGB',l.rgbBands,'cfa.rgb.RGB.tif',bits=bits)
		l.stiff('CFA',l.xyzBands,'cfa.cfa.XYZ.tif',bits=bits)
		l.stiff('RGB',l.xyzBands,'cfa.rgb.XYZ.tif',bits=bits)
		l.stiff('CFA',('Y'),'cfa.cfa.L.tif',bits=bits)
		l.stiff('RGB',('Y'),'cfa.rgb.L.tif',bits=bits)


	if int(cfg['do_rgb_process'])==1:
		fits={'B': './OUTPUT/result/stacked.Bi.fit', 'G': './OUTPUT/result/stacked.Gi.fit', 'R': './OUTPUT/result/stacked.Ri.fit'}
		l=ColorMixer(fits,gamma=gamma)
		l.rgb2xyz()
		l.stiff('RGB',l.rgbBands,'rgb.rgb.RGB.tif',bits=bits)
		l.stiff('RGB',l.xyzBands,'rgb.rgb.XYZ.tif',bits=bits)
		l.stiff('RGB',('Y'),'rbg.rgb.L.tif',bits=bits)


