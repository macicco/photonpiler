#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import Image, ImageDraw, ImageFilter
import numpy as np
import os,commands
import pyexiv2
import datetime
import scipy.signal
import math

def gauss_kern(size, sizey=None):
    	""" Returns a normalized 2D gauss kernel array for convolutions """
    	size = int(size)
    	if not sizey:
        	sizey = size
    	else:
        	sizey = int(sizey)
    	x, y = np.mgrid[-size:size+1, -sizey:sizey+1]
    	g = np.exp(-(x**2/float(size)+y**2/float(sizey)))
    	return g / g.sum()





#Adapted from http://en.wikipedia.org/wiki/Otsu%27s_method
#Not finished!!
def otsu(image):
    histsize=50
    im=Image.open(image)
    gray=im.convert('L')
    bw = np.asarray(gray).copy()
    total=bw.size
    histogram=np.histogram(bw,bins=histsize,density=False)[0]
    print histogram
    sum = 0
    for i in range(0,histsize):
        sum += i * histogram[i]
    sumB = 0
    wB = 0
    wF = 0
    max = 0.0
    between = 0.0
    threshold1 = 0.0
    threshold2 = 0.0
    for i in range(0,histsize): 
        wB += histogram[i]
        if (wB == 0):
            continue
        wF = total - wB
        if (wF == 0):
            break
        sumB += i * histogram[i]
        mB = sumB / wB
        mF = (sum - sumB) / wF
        between = wB * wF * math.pow(mB - mF, 2)
        if ( between >= max ):
            threshold1 = i
            if ( between > max ):
                threshold2 = i
            max = between            

    return ( threshold1 + threshold2 ) / 2.0;

def medfilt (x, k):
    """Apply a length-k median filter to a 1D array x.
    Boundaries are extended by repeating endpoints.
    """
    assert k % 2 == 1, "Median filter length must be odd."
    assert x.ndim == 1, "Input must be one-dimensional."
    k2 = (k - 1) // 2
    y = np.zeros ((len (x), k), dtype=x.dtype)
    y[:,k2] = x
    for i in range (k2):
        j = k2 - i
        y[j:,i] = x[:-j]
        y[:j,i] = x[0]
        y[:-j,-(i+1)] = x[j:]
        y[-j:,-(i+1)] = x[-1]
    return np.median (y, axis=1)

def threshold(image):
	'''
	Search the rigthmost minima of the histogram
	'''
	im=Image.open(image)
	gray=im.convert('L')
	bw = np.asarray(gray).copy()
	hist=np.histogram(bw,bins=50,density=False)
	print hist
	extrema=scipy.signal.argrelextrema(hist[0],np.less,order=2)
	print extrema
	print extrema[0][-1]
	return hist[1][extrema[0][-1]]



def binarize(image,nsigma):
	im=Image.open(image)
	gray=im.convert('L')
	draw = ImageDraw.Draw(gray)
	bw = np.asarray(gray).copy()
	kernel=gauss_kern(3)
	bw=scipy.signal.convolve(bw,kernel)
	mean=bw.mean()
	std=bw.std()
	h=mean+nsigma*std
	#h=threshold(image)
	#h=otsu(image)
	print std,mean,h
	bw[bw < h] = 0    # Black
	bw[bw >= h] = 255 # White
	# Now we put it back in Pillow/PIL land
	binarized=Image.fromarray(bw).convert('1')
	draw = ImageDraw.Draw(binarized)
	b=binarized.getbbox()
	print b
	draw.rectangle(b,outline=1)
	del draw
	binarized.save(image+'.binary.jpg')
	return binarized

def contour(image):
	im=Image.open(image)
	con=im.filter(ImageFilter.SMOOTH_MORE)
	con.save(image+"_contour.png")

def bbox(image,nsigma):
	binary=binarize(image,nsigma)
	b=binary.getbbox()
	print b

	tam=max((b[2]-b[0]),(b[3]-b[1]))
	x0,y0=(b[2]+b[0])/2,(b[3]+b[1])/2
	print tam,x0,y0
	newbb=(x0-tam,y0-tam,x0+tam,y0+tam)
	print newbb
	metadata = pyexiv2.ImageMetadata(image)
	metadata.read()
	tag = metadata['Exif.Image.DateTime']
	print "Exiv2 time:",tag.raw_value
	t=tag.value - datetime.timedelta(seconds=15*60)
	name=t.strftime('%H:%M:%S')
	im=Image.open(image)
	cropped=im.crop(newbb)
	cropped.save(name+".cropped.jpg")

def searchJpgFiles(path,extension='.JPG'):
	l=[]
	for file in os.listdir(path):
	    if file.endswith(extension):
		l.append(path+"/"+file)
	return l

def normalize(arr):
    """
    Linear normalization
    http://en.wikipedia.org/wiki/Normalization_%28image_processing%29
    """
    arr = np.asarray(arr).copy()
    print arr.shape()
    # Do not touch the alpha channel
    for i in range(3):
        minval = arr[...,i].min()
        maxval = arr[...,i].max()
        if minval != maxval:
            arr[...,i] -= minval
            arr[...,i] *= (255.0/(maxval-minval))
    return Image.fromarray(arr)



if __name__ == '__main__':

	for jpg in searchJpgFiles('.','.jpg'):
		print jpg
		bbox(jpg,2.5)

	'''
	threshold("IMG_7459.JPG")
	'''




