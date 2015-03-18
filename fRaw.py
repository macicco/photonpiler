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
		if int(cfg['600d_bandmap'])==1:
			#Canon 600D
			self.BandMap={'Ri':'Gi2','Gi1':'Ri','Gi2':'Bi','Bi':'Gi1','P':'P'}
		else:
			#PLAIN
			self.BandMap={'Ri':'Ri','Gi1':'Gi1','Gi2':'Gi2','Bi':'Bi','P':'P'}

		lightRaws=self.searchRawFiles(cfg['rawsdir']+'/'+cfg['lightsdir'])
		darkRaws=self.searchRawFiles(cfg['rawsdir']+'/'+cfg['darksdir'])
		flatRaws=self.searchRawFiles(cfg['rawsdir']+'/'+cfg['flatsdir'])
		self.rawFrames={'lights':lightRaws,'darks':darkRaws,'flats':flatRaws}

		#self.bands=cfg['bands'].split(',')

		bands=[]

		if int(cfg['do_rgb_process'])==1:
			bands=['Ri','Gi1','Gi2','Bi']


		if int(cfg['do_cfa_process'])==1:
			if len(bands)==0:
				bands=['P']
			else:
				bands.append('P')


		self.bands=bands
		print self.bands
		self.createOutputDirs()

		print "BANDS:",self.bands
		for i,B in enumerate(self.bands):
			self.doBand(B)


	def doBand(self,band):
		print "Do band:",band
		cfg=self.cfg
		frames=self.rawFrames
		iband=self.BandMap[band]

		raws=frames['darks']
		outdir=self.DIRS[band]['darksdir']
		masterdark_filename=outdir+'/'+cfg['masterdark']+'.'+band+'.fit'
		self.num={'darks':0,'flats':0}
		self.fitFrames={}
		
		'''Check if premaded dark its present'''
		readyDark=cfg['rawsdir']+'/'+cfg['darksdir']+'/'+cfg['masterdark']+'.'+band+'.fit'
		if  os.path.exists(readyDark):
			print "Dark master fits present. Coping:",readyDark
			strCmd= 'cp -v '+readyDark+ " " + masterdark_filename
			print strCmd
			res=commands.getoutput(strCmd)
			print res


		
		if not os.path.exists(masterdark_filename):
			darkFits=self.rawtran(raws,band,outdir=outdir,dark=False,flat=False,rotate=False)
			self.num['darks']=len(darkFits)
			self.fitFrames['darks']=darkFits
			if self.num['darks']!=0:
				masterdark=self.MasterDark()
				masterdark.save(masterdark_filename)
		else:
			print masterdark_filename," already exist. Deleted if you wan to reprocess"

		raws=frames['flats']
		outdir=self.DIRS[band]['flatsdir']
		masterflat_filename=outdir+'/'+cfg['masterflat']+'.'+band+'.fit'

		'''Check if premaded flat its present'''
		readyFlat=cfg['rawsdir']+'/'+cfg['flatsdir']+'/'+cfg['masterflat']+'.'+band+'.fit'
		if  os.path.exists(readyFlat):
			print "Dark flat fits present. Coping:",readyFlat
			strCmd= 'cp -v '+readyFlat+ " " + masterflat_filename
			print strCmd
			res=commands.getoutput(strCmd)
			print res			


		if not os.path.exists(masterflat_filename):
			flatFits=self.rawtran(raws,band,outdir=outdir,dark=True,flat=False,rotate=False)
			self.num['flats']=len(flatFits)
			self.fitFrames['flats']=flatFits
			if self.num['flats']!=0:
				masterflat=self.MasterFlat()
				masterflat.save(masterflat_filename)
		else:
			print masterflat_filename," already exist. Deleted if you wan to reprocess"

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
			try:
				header['CCD-TEMP']=float(exiftags['CameraTemperature'].replace(' ','').replace('C',''))
			except:
				print "Not CCD temp tag"
			header['COMMENT']="ORIGINAL EXIF DATA BEGIN:"
			for exifkey in exiftags.keys():
				header['COMMENT']="EXIF:: "+exifkey+":"+str(exiftags[exifkey])
			header['COMMENT']="ORIGINAL EXIF DATA END:"


	def rawtran(self,raws,band,outdir,bias=True,dark=True,flat=True,rotate=False):
		cfg=self.cfg
		iband=self.BandMap[band]
		l=[]
		print raws
		for raw in raws:
			outfile=outdir+"/"+os.path.basename(raw).replace(cfg['ext'],band+'.fit')
			if not os.path.exists(outfile):
				print ".-.-.-."
				print "rawtran-ting:",outfile
				strCmd= 'rawtran -X "-t 0" -c '+iband+' -B -32 -o '+outfile+ " " + raw
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
				if bias:
					superbias=cfg['superbias']
					print superbias
					if os.path.exists(superbias):
						print "Superbias"
						light=fitsMaths.fitMaths(outfile)
						superbias=fitsMaths.fitMaths(superbias)
						light=light-superbias
						light.save(outfile)			
				if flat:
					flatfile=self.DIRS[band]['flatsdir']+'/'+cfg['masterflat']+'.'+band+'.fit'
					if os.path.exists(flatfile):
						light=fitsMaths.fitMaths(outfile)
						light=light.flat(flatfile)
						light.save(outfile)
					else:
						print flatfile," not found"
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


