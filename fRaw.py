#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import os,commands
import pyfits
import numpy as np
import simplejson

import fitsMaths
import fConfig


class raw2fits():
	'''
	This class  generate instrumental bands FITs from RAW DSLR photos
	'''
	def __init__(self):
		config=fConfig.fConfig()
		cfg=config.getSection('RAW')
		self.cfg=cfg
		self.bands=config.bands
		self.BandMap=config.BandMap
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
		outdir=self.DIRS[band]['darksdir']
		darkFits=self.rawtran(raws,band,outdir=outdir,dark=False,flat=False,rotate=False)
		self.num={'darks':len(darkFits)}
		self.fitFrames={'darks':darkFits}
		masterdark=self.MasterDark()
		masterdark.save(outdir+'/'+cfg['masterdark']+'.'+band+'.fit')

		raws=frames['flats']
		outdir=self.DIRS[band]['flatsdir']
		flatFits=self.rawtran(raws,band,outdir=outdir,dark=True,flat=False,rotate=True)
		self.num['flats']=len(flatFits)
		self.fitFrames['flats']=flatFits
		masterflat=self.MasterFlat()
		masterflat.save(outdir+'/'+cfg['masterflat']+'.'+band+'.fit')

		raws=frames['lights']
		outdir=self.DIRS[band]['lightsdir']
		lightFits=self.rawtran(raws,band,outdir=outdir,dark=True,flat=True,rotate=False)
		self.num['lights']=len(lightFits)
		self.fitFrames['lights']=lightFits



	def createOutputDirs(self):
		cfg=self.cfg
		frametypes=['darksdir','flatsdir','lightsdir','rawfits']
		dirs={}
		for t in frametypes:
			dirs[t]=cfg[t]
		if not os.path.exists(cfg['fitsdir']):
			os.makedirs(cfg['fitsdir'])
		self.DIRS={}
		for B in self.bands:
			if not os.path.exists(cfg['fitsdir']+'/'+B):
				os.makedirs(cfg['fitsdir']+'/'+B)
			#print "Creating FITs dirs:",dirs
			dummy={}
			for t in frametypes:
				dd=cfg['fitsdir']+'/'+B+'/'+dirs[t]
				if not os.path.exists(dd):
					os.makedirs(dd)
				else:
					print "Dir: ",dd," already exist"
				dummy[t]=dd
			self.DIRS[B]=dummy
		print 	self.DIRS

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
				rawfits=self.DIRS[band]['rawfits']+"/"+os.path.basename(raw).replace(cfg['ext'],band+'.fit')
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
					darkfile=self.DIRS[band]['darksdir']+'/'+cfg['masterdark']+'.'+band+'.fit'
					if os.path.exists(darkfile):
						light=fitsMaths.fitMaths(outfile)
						light=light.dark(darkfile)
						light.save(outfile)				
				if flat:
					flatfile=self.DIRS[band]['darksdir']+'/'+cfg['masterflat']+'.'+band+'.fit'
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


