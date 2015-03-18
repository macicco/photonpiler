#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import os,commands
import pyfits
import numpy as np
import simplejson

import fitsMaths
import fConfig

import fRaw
import fRegistrarTriangles
import fColorMixer

if __name__ == '__main__':

	engine=fRaw.raw2fits()

	co=fRegistrarTriangles.registrarTriangle()
	if int(co.cfg['do_cfa_process'])==1:
		cfafits=co.doCFA(combine='median')

	if int(co.cfg['do_rgb_process'])==1:
		rgbfits=co.doRGB(combine='median')

	config=fConfig.fConfig()
	cfg=config.getSection('COLORMIXER')
	gamma=float(cfg['gamma'])
	bits=float(cfg['bits'])
	if int(cfg['do_cfa_process'])==1:
		l=fColorMixer.ColorMixer(cfafits,gamma=gamma)
		l.cfa2xyz()
		l.rgb2xyz()
		l.stiff('CFA',l.rgbBands,'cfa.cfa.RGB.tif',bits=bits)
		l.stiff('RGB',l.rgbBands,'cfa.rgb.RGB.tif',bits=bits)
		l.stiff('CFA',l.xyzBands,'cfa.cfa.XYZ.tif',bits=bits)
		l.stiff('RGB',l.xyzBands,'cfa.rgb.XYZ.tif',bits=bits)
		l.stiff('CFA',('Y'),'cfa.cfa.L.tif',bits=bits)
		l.stiff('RGB',('Y'),'cfa.rgb.L.tif',bits=bits)


	if int(cfg['do_rgb_process'])==1:
		l=fColorMixer.ColorMixer(rgbfits,gamma=gamma)
		l.rgb2xyz()
		l.stiff('RGB',l.rgbBands,'rgb.rgb.RGB.tif',bits=bits)
		l.stiff('RGB',l.xyzBands,'rgb.rgb.XYZ.tif',bits=bits)
		l.stiff('RGB',('Y'),'rgb.rgb.L.tif',bits=bits)
