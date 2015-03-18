#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import os,commands
import pyfits
import numpy as np
import simplejson

import fitsMaths
import fConfig


class makebias():
	'''
	This class  generate instrumental bands FITs from RAW DSLR photos
	'''
	def __init__(self):
		self.ext='CR2'
		biasRaws=self.searchRawFiles('.')
		biasFits=self.rawtran(biasRaws,'P',outdir='.')
		r=fitsMaths.combineFits(biasFits,combine='median')
		r.save('superbias.fit')



	def searchRawFiles(self,path):
		l=[]
		extension='.'+self.ext
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


	def rawtran(self,raws,band,outdir):
		l=[]
		print raws
		for raw in raws:
			outfile=outdir+"/"+os.path.basename(raw).replace(self.ext,band+'.fit')
			if not os.path.exists(outfile):
				print ".-.-.-."
				print "rawtran-ting:",outfile
				strCmd= 'rawtran -X "-t 0" -c '+band+' -B -32 -o '+outfile+ " " + raw
				print strCmd
				res=commands.getoutput(strCmd)
				print res
				'''Copy exif information to fit'''
				self.exif2fit(raw,outfile)
				rawfits=outdir+"/"+os.path.basename(raw).replace(self.ext,band+'.fit')

			else:
				print "Already exist:",outfile
			l.append(outfile)
		return l




if __name__ == '__main__':
	engine=makebias()


