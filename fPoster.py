#!/usr/bin/python
#-*- coding: iso-8859-15 -*-
#NACHO MAS
import os,commands

import PIL.ImageOps
import Image, ImageDraw, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import  A6,A5,A4, A3,A2,A1, A0, landscape, portrait 
	
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont




def searchJpgFiles(path,extension='.JPG'):
	l=[]
	for file in os.listdir(path):
	    if file.endswith(extension):
		l.append(file)
	l.sort()
	return l

def resize(jpg,basewidth = 100):	
	img = Image.open(jpg)
	wpercent = (basewidth/float(img.size[0]))
	hsize = int((float(img.size[1])*float(wpercent)))
	#img = img.resize((basewidth,hsize), Image.ANTIALIAS)
	img = img.resize((basewidth,hsize))
	return img



def objBook(inv=0):
	imsize=71
	sep=5
	x=30
	y=paperheight-sep*2-imsize
	pagina=1

	for jpg in searchJpgFiles('.','.cropped.jpg'):
		# x2 para tener mas calidad
		image = resize(jpg,imsize*3)
		print jpg
		hora,dummy,dummy=jpg.split('.')
		if inv==1:
			inverted_image = PIL.ImageOps.invert(image)
			inverted_image.save(jpg+'_inverted.jpg')
			c.drawImage(jpg+'_inverted.jpg',x,y+10,imsize,imsize)
		else:	
			pass
			image.save(jpg+'_resize.jpg')
			c.drawImage(jpg+'_resize.jpg',x,y+10,imsize,imsize)			
		c.drawString(x+22,y+2,hora)


		x=x+sep+imsize
		if (x+imsize+sep)>paperwidth:
			x=30
			y=y-sep*2-imsize
		if y<sep:
			c.setFont("Helvetica", 22)
			c.drawString(2000,200,pie0)
			c.setFont("Helvetica", 8)
			c.drawString(2000,10,pie1)
			c.drawString(paperwidth-40,10,'Pag.'+str(pagina))
			pagina=pagina+1
			x=20
			y=paperheight-sep*2-imsize
			c.showPage()


	c.setFont("Helvetica", 26)
	c.drawString(400,155,pie0)
	c.setFont("Helvetica", 10)
	c.drawString(400,140,"Canon 450D timelapse under bad wheather. Timestamp from Exiv2 (UTC). Optics: Meade LX75 6\" Newton")
	c.drawString(900,15,pie1)
	'''
	c.drawString(20,20,pie0)
	c.drawString(20,10,pie1)
	c.drawString(paperwidth-40,10,'Pag.'+str(pagina))
	'''
	c.showPage()
	c.save()



if __name__ == '__main__':
	pdfmetrics.registerFont( TTFont( 'arial', 'arial.ttf') )
	#paper=portrait(A4)
	paper=landscape(A3)
	paperwidth, paperheight = paper
	c = canvas.Canvas('eclipse_poster.pdf', pagesize=paper)
	c.setFont("Helvetica", 7)
	c.rect(0, 0, paperwidth, paperheight, stroke=0,fill=1)
	c.setFillColorRGB(100,100,100) 
	pie0="Madrid March 20, 2015 Solar Eclipse"
	pie1="Copyright:Fernando Fernandez. Cienciactiva. March 2015"
	objBook()
