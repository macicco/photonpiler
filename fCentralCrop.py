#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import Image, ImageDraw, ImageFilter
import numpy as np
import os,commands
import pyexiv2
import datetime
import scipy.signal
import math



def bbox(image,margen):
	im=Image.open(image)
	width, height =im.size
	tamX=width*margen/100
	tamY=height*margen/100
	newbb=(tamX,tamY,width-tamX,height-tamY)
	print newbb
	metadata = pyexiv2.ImageMetadata(image)
	metadata.read()
	tag = metadata['Exif.Image.DateTime']
	print "Exiv2 time:",tag.raw_value
	t=tag.value - datetime.timedelta(seconds=15*60)
	name=t.strftime('%H:%M:%S')
	
	cropped=im.crop(newbb)
	cropped.save(name+".cropped.jpg")

def searchJpgFiles(path,extension='.JPG'):
	l=[]
	for file in os.listdir(path):
	    if file.endswith(extension):
		l.append(path+"/"+file)
	return l



if __name__ == '__main__':

	for jpg in searchJpgFiles('.','.JPG'):
		print jpg
		bbox(jpg,30)

	'''
	threshold("IMG_7459.JPG")
	'''




