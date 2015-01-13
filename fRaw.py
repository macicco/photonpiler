#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import os,commands
import pyfits
import numpy as np
import fConfig
import simplejson
import fitsMaths



class raw2fits():
	'''
	This class  generate instrumental bands FITs from RAW DSLR photos
	'''
	def __init__(self):
		cfg=fConfig.fConfig().getSection('RAW')
		self.cfg=cfg
		self.bands=['Ri','Gi1','Gi2','Bi']
		self.BandMap={'Ri':'Gi2','Gi1':'Ri','Gi2':'Bi','Bi':'Gi1','u':'u'}
		lightRaws=self.searchRawFiles(cfg['rawsdir']+'/'+cfg['lightsdir'])
		darkRaws=self.searchRawFiles(cfg['rawsdir']+'/'+cfg['darksdir'])
		flatRaws=self.searchRawFiles(cfg['rawsdir']+'/'+cfg['flatsdir'])
		self.rawFrames={'lights':lightRaws,'darks':darkRaws,'flats':flatRaws}

		self.createOutputDirs()
		for i,B in enumerate(self.bands):
			self.doBand(i)


	def doBand(self,iband):
		cfg=self.cfg
		frames=self.rawFrames
		band=self.bands[iband]
		raws=frames['darks']
		outdir=cfg['fitsdir']+'/'+cfg['darksdir']
		darkFits=self.rawtran(raws,band,outdir=outdir,dark=False,flat=False,rotate=False)
		self.num={'darks':len(darkFits)}
		self.fitFrames={'darks':darkFits}
		masterdark=self.MasterDark()
		masterdark.save(cfg['masterdark']+'.'+band+'.fit')

		raws=frames['flats']
		outdir=cfg['fitsdir']+'/'+cfg['flatsdir']
		flatFits=self.rawtran(raws,band,outdir=outdir,dark=True,flat=False,rotate=True)
		self.num['flats']=len(flatFits)
		self.fitFrames['flats']=flatFits
		masterflat=self.MasterFlat()
		masterflat.save(cfg['masterflat']+'.'+band+'.fit')

		raws=frames['lights']
		outdir=cfg['fitsdir']+'/'+cfg['lightsdir']
		lightFits=self.rawtran(raws,band,outdir=outdir,dark=True,flat=True,rotate=False)
		self.num['lights']=len(lightFits)
		self.fitFrames['lights']=lightFits



	def createOutputDirs(self):
		cfg=self.cfg
		dirs=[cfg['darksdir'],cfg['flatsdir'],cfg['lightsdir'],cfg['rawfits']]
		if not os.path.exists(cfg['fitsdir']):
			os.makedirs(cfg['fitsdir'])
		dirs=map(lambda x:cfg['fitsdir']+'/'+x,dirs)
		#print "Creating FITs dirs:",dirs
		for d in dirs:
			if not os.path.exists(d):
				os.makedirs(d)
			else:
				print "Dir: ",d," already exist"

	def searchRawFiles(self,path):
		l=[]
		cfg=self.cfg
		extension='.'+cfg['ext']
		for file in os.listdir(path):
		    if file.endswith(extension):
			l.append(path+"/"+file)
		return l
			
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


	def rawtran(self,raws,band,outdir,dark=True,flat=True,rotate=False):
		cfg=self.cfg
		iband=self.BandMap[band]
		l=[]
		print raws
		for raw in raws:
			outfile=outdir+"/"+os.path.basename(raw).replace(cfg['ext'],band+'.fit')
			if not os.path.exists(outfile):
				print ".-.-.-."
				print "rawtran-ting:",outfile
				strCmd= 'rawtran -c '+iband+' -B -32 -o '+outfile+ " " + raw
				print strCmd
				res=commands.getoutput(strCmd)
				print res
				'''Copy exif information to fit'''
				self.exif2fit(raw,outfile)
				rawfits=cfg['fitsdir']+"/"+cfg['rawfits']+"/"+os.path.basename(raw).replace(cfg['ext'],band+'.fit')
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
					darkfile=cfg['masterdark']+'.'+band+'.fit'
					if os.path.exists(darkfile):
						light=fitsMaths.fitMaths(outfile)
						light=light.dark(darkfile)
						light.save(outfile)				
				if flat:
					flatfile=cfg['masterflat']+'.'+band+'.fit'
					if os.path.exists(flatfile):
						light=fitsMaths.fitMaths(outfile)
						light=light.flat(flatfile)
						light.save(outfile)
			else:
				print "Already exist:",outfile
			l.append(outfile)
		return l

	def MasterFlat(self,op='median'):
		superflat=fitsMaths.combineFits(self.fitFrames['flats'],combine=op)
		maxi=superflat.hdulist[0].data.mean()
		superflat=(1./maxi)*superflat
		print "Renormalizing mean/std:",superflat.hdulist[0].data.mean(),superflat.hdulist[0].data.std()
		return superflat

	def MasterDark(self,op='median'):
		print self.fitFrames['darks']
		return fitsMaths.combineFits(self.fitFrames['darks'],combine=op)


if __name__ == '__main__':
	engine=raw2fits()


