#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import os,commands
import numpy as np
from scipy.stats import sigmaclip
from scipy.ndimage.interpolation import shift

import fitsMaths
import fRegistrarBase
import demosaic

'''
Triangle registration
No astrometric catalog needed
'''
class registrarTriangle(fRegistrarBase.registrarBase):

	def getTriangles(self):
		numstars=20
		maxtriangles=numstars*(numstars-1)*(numstars-2)/6
		dt=np.dtype([('frame',int),('v0',int),('v1',int),('v2',int),('sA',float),('sB',float),('points',np.float32,(3,2))])
		result=np.zeros((maxtriangles*len(self.fitFrames['lights'][self.BaseBand]),),dtype=dt)
		triInx=0
		for k,light in enumerate(self.fitFrames['lights'][self.BaseBand]):
			print "Searching triangles on:",light
			a=np.asarray(self.sex(light))
			#get only the 20 brighter stars
			b=a[['NUMBER','MAG_AUTO','X_IMAGE','Y_IMAGE']]
			c=np.sort(b,order='MAG_AUTO')
			d=np.sort(c[:numstars],order='NUMBER')
			for s in d:
				id0=s['NUMBER']
				flt=(d['NUMBER']!=id0)
				dd=d[flt]
				for ss in dd:
					id1=ss['NUMBER']
					if id1<id0:
						continue

					flt=(dd['NUMBER']!=id1)
					ddd=dd[flt]
					for sss in ddd:
						id2=sss['NUMBER']
						if id2<id1:
							continue
						result[triInx]['frame']=k
						result[triInx]['v0']=id0
						result[triInx]['v1']=id1
						result[triInx]['v2']=id2
						result[triInx]['points'][0][0]=s['X_IMAGE']
						result[triInx]['points'][0][1]=s['Y_IMAGE']
						result[triInx]['points'][1][0]=ss['X_IMAGE']
						result[triInx]['points'][1][1]=ss['Y_IMAGE']
						result[triInx]['points'][2][0]=sss['X_IMAGE']
						result[triInx]['points'][2][1]=sss['Y_IMAGE']

						t=result[triInx]['points']
						dis=np.zeros(3)
						dis[0]=self.distance(t[0],t[1])
						dis[1]=self.distance(t[0],t[2])
						dis[2]=self.distance(t[1],t[2])
						#reorder by distance a->b->c
						dis=np.sort(dis)
						sA=dis[2]/dis[0]
						sB=dis[1]/dis[0]

						result[triInx]['sA']=sA
						result[triInx]['sB']=sB

						triInx=triInx+1
		print "Triangles real/theory",triInx,maxtriangles*len(self.fitFrames['lights'][self.BaseBand])
		self.result=result

	def match(self):
		triErr=0.001
		result=self.result
		dt=np.dtype([('frame',int),('err',float),('refpoints',np.float32,(3,2)),('points',np.float32,(3,2))])
		matchedTriangles=np.zeros((1,),dtype=dt)
		matchedBuffer=np.zeros((1,),dtype=dt)
		matchCount=0
		for k,light in enumerate(self.fitFrames['lights'][self.BaseBand]):
			if k==0:
				frame0=np.sort(result[(result['frame']==0)],order='sA')
				continue
			frame=np.sort(result[(result['frame']==k)],order='sA')
			for t0Inx,triangle0 in enumerate(frame0):
				t0=(triangle0['sA'],triangle0['sB'])
				p=triangle0['points']
				for tInx,triangle in enumerate(frame):
					tt=(triangle['sA'],triangle['sB'])
					pp=triangle['points']	
					if tt[0]-t0[0]>=triErr:
						break			
					dd=self.distance(t0,tt)
					if dd <= triErr :
						if matchCount==0:
							matchedTriangles['frame']=k
							matchedTriangles['err']=dd
							matchedTriangles['refpoints']=p
							matchedTriangles['points']=pp
						else:
							matchedBuffer['frame']=k
							matchedBuffer['err']=dd
							matchedBuffer['refpoints']=p
							matchedBuffer['points']=pp
							matchedTriangles=np.vstack((matchedTriangles,matchedBuffer))
						#print "Match",k,dd,t0,tt
						#print p
						#print pp
						#print np.average((pp-p),axis=0)
						matchCount=matchCount+1
		print matchCount
		self.matchedTriangles= matchedTriangles
		return matchedTriangles

	def matchThread(self):
		'''
		TO BE DONE
		'''
		pass

	def homografy(self):
		matchedTriangles=self.matchedTriangles
		homo={}
		for k,light in enumerate(self.fitFrames['lights'][self.BaseBand]):
			if k==0:
				continue
			matchedTri=np.sort(matchedTriangles[(matchedTriangles['frame']==k)])
			print "FRAME:",k," MATCHED TRIANGLES:",len(matchedTri)
			result=np.array([[0,0],[0,0],[0,0]])
			for i,match in enumerate(matchedTri):
				err=match['err']
				p0=match['refpoints']
				p1=match['points']
				diff=p1-p0
				if i==0:
					result=np.array(diff)
				else:
					result=np.vstack((result,diff))
				trian=np.average(diff,axis=0)
			print "Sigmaclip and averaging.."
			xx,xlow,xhigh=sigmaclip(result[:,0],low=self.nsigma,high=self.nsigma)
			yy,ylow,yhigh=sigmaclip(result[:,1],low=self.nsigma,high=self.nsigma)
			x=xx.mean()
			y=yy.mean()
			#print xx,yy
			if np.isnan(x):
				x=0
			if np.isnan(y):
				y=0
			homo[k]={'x':x,'y':y}
			print homo[k]
			print
		self.homo=homo

	def stack(self,band,combine='median',cfaframe=False):
		xdeltaMax=0
		xdeltaMin=0
		ydeltaMax=0
		ydeltaMin=0
		fitsList=[]
		lightlist=self.fitFrames['lights'][band]
		for k,light in enumerate(lightlist):
			if k==0:
				fitsList.append(light)
				continue	
			print "Frame",light,k	
			homo=self.homo
			frame=fitsMaths.fitMaths(light)
			x=homo[k]['x']	
			y=homo[k]['y']
			if cfaframe:
				x_=2*np.round(x/2.)
				y_=2*np.round(y/2.)
			else:
				x_=x
				y_=y
			print "Shifting:",x_,y_
			frame.hdulist[0].data=shift(frame.hdulist[0].data,(-y_,-x_))
			shiftedlight=self.cfg['workdir']+'/'+band+'/'+os.path.basename(light).replace('IMG','_IMG')
			frame.save(shiftedlight)
			fitsList.append(shiftedlight)
		if not os.path.exists(self.cfg['resultdir']):
			os.makedirs(self.cfg['resultdir'])

		outfile=self.cfg['resultdir']+"/stacked."+band+".fit"
		Master=fitsMaths.combineFits(fitsList,combine=combine)
		Master.save(outfile)
		return outfile

	def distance(self,p0,p1):
		return np.sqrt((p1[0]-p0[0])**2+(p1[1]-p0[1])**2)

	def doRGB(self,combine='median',baseband='Gi1'):
		'''
		Process and stack individualy each band
		'''
		bands=['Ri','Gi1','Gi2','Bi']
		rgbBands={'Ri':'R','Gi':'G','Bi':'B','Gi1':'Gi1','Gi2':'Gi2'}
		self.BaseBand=baseband

		bands.remove(baseband)
		print "BASE BAND:",baseband
		print self.fitFrames
		if len(self.fitFrames['lightsBase'][self.BaseBand])>1:
			self.rankFrames(self.BaseBand)
			self.getTriangles()
			self.match()
			self.homografy()
		else:
			self.fitFrames['lights'][self.BaseBand]=self.fitFrames['lightsBase'][self.BaseBand]

		destdir=self.cfg['workdir']+'/'+self.BaseBand
		if not os.path.exists(destdir):
			os.makedirs(destdir)
		filename=self.stack(baseband,combine=combine)
		outfiles={baseband:filename}
		print "Other bands:",bands
		
		for i,B in enumerate(bands):
			self.fitFrames['lights'][B]=[]

		for f,light in enumerate(self.fitFrames['lights'][self.BaseBand]):
  		    for i,B in enumerate(bands):
			destdir=self.cfg['fitsdir']+'/'+B+'/'+self.cfg['lightsdir']
			if not os.path.exists(destdir):
				os.makedirs(destdir)
			lightRGB=destdir+'/'+os.path.basename(light).replace(self.BaseBand,B)
			print lightRGB
			self.fitFrames['lights'][B].append(lightRGB)		



		for B in bands:
			print "Band:",B
			destdir=self.cfg['workdir']+'/'+B
			if not os.path.exists(destdir):
				os.makedirs(destdir)
			filename=self.stack(B,combine=combine)
			outfiles[rgbBands[B]]=filename

		'''combine Gi1 and Gi2 '''
		Gi=fitsMaths.combineFits((outfiles['Gi1'],outfiles['Gi2']),combine='median')
		filename=self.cfg['resultdir']+"/stacked.Gi.fit"
		Gi.save(filename)
		outfiles.pop("Gi1", None)
		outfiles.pop("Gi2", None)
		outfiles[rgbBands['Gi']]=filename
		return outfiles

	def doCFA(self,combine='median'):
		'''
		Process and stack band P(raw) and then
		extrack each band from it
		'''
		self.BaseBand='P'

		print "Luminance band:",self.BaseBand
		print self.fitFrames['lightsBase'][self.BaseBand]
		#self.fitFrames['lights']={}
		if len(self.fitFrames['lightsBase'][self.BaseBand])>1:
			self.rankFrames(self.BaseBand)
			self.getTriangles()
			self.match()
			self.homografy()
		else:
			print "Single frame"
			self.fitFrames['lights']={}
			self.fitFrames['lights'][self.BaseBand]=self.fitFrames['lightsBase'][self.BaseBand]

		destdir=self.cfg['workdir']+'/'+self.BaseBand
		if not os.path.exists(destdir):
			os.makedirs(destdir)
		filename=self.stack(self.BaseBand,combine=combine,cfaframe=True)
		outfiles={self.BaseBand:filename}

		bands=['R','G','B']
		print "Other bands:",bands
		'''Creating R,G,B bands fits from CFA '''
		for i,B in enumerate(bands):
			self.fitFrames['lights'][B]=[]
		for f,light in enumerate(self.fitFrames['lights'][self.BaseBand]):
			print "Demosaic:",light
			frame=fitsMaths.fitMaths(light)
			cfa=frame.hdulist[0].data/frame.hdulist[0].data.max()
			mosaicStack=demosaic.demosaic(cfa,pattern='rggb',method='bilinear')
			for i,B in enumerate(bands):
				print "Band:",B
				destdir=self.cfg['workdir']+'/'+B
				if not os.path.exists(destdir):
					os.makedirs(destdir)
				lightRGB=destdir+'/'+os.path.basename(light).replace(self.BaseBand,B)
				print lightRGB
				frame.hdulist[0].data=mosaicStack[:,:,i]
				frame.save(lightRGB)
				self.fitFrames['lights'][B].append(lightRGB)
				
		######HASTA AQUI
		print self.fitFrames['lights']
		for B in bands:
			print "Band:",B
			filename=self.stack(B,combine=combine)
			outfiles[B]=filename

		return outfiles





if __name__ == '__main__':
	'''

	'''
	co=registrarTriangle()
	if int(co.cfg['do_cfa_process'])==1:
		co.doCFA(combine='median')

	if int(co.cfg['do_rgb_process'])==1:
		co.doRGB(combine='median')	








	
