__Photonpiler__
========
Introduction
------------
Photonpiler is a collection of python scripts aim to process digital astrophotografies.

This software use numpy, rawtran and sextractor thus you have to have installed in your system.

__Installing__
----------
Download and put in a directory of your election inside your binary path. Edit photonpiler.cfg and adapt to your needs some parameters.

__Use__
-------
This are the steps:

Create a directory tree like this:

	[nameofyourelection]	- SCIENCE
				- FLATS
				- DARKS

Put your RAW photos in its corresponding directories.

Edit photonpiler.cfg and set do_cfa_process=1 or do_rgb_process=1 or both. 

do_cfa_process=1 
Means do all the alinement with the CFA frames and then demosaic stacked frame

do_rgb_process=1 
Means do all processing (alignment and stacking) per separate channels.



RUN:

cd [nameofyourelection]
./fRaw.py
./fRegistrarTriangles.py
./fColorMixer.py

The result images go to [nameofyourelection] directory. Several images are create:






