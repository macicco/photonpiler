#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import os,commands
import numpy as np
from scipy.stats import sigmaclip
from scipy.ndimage.interpolation import shift

import fitsMaths
import fRegistrarBase


'''
Triangle registration
No astrometric catalog needed
'''
class registrarTriangle(fRegistrarBase.registrarBase):

	def getTriangles(self):
		numstars=20
		maxtriangles=numstars*(numstars-1)*(numstars-2)/6
		dt=np.dtype([('frame',int),('v0',int),('v1',int),('v2',int),('sA',float),('sB',float),('points',np.float32,(3,2))])
		result=np.zeros((maxtriangles*len(self.fitFrames['lights']),),dtype=dt)
		triInx=0
		for k,light in enumerate(self.fitFrames['lights']):
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
		print "Triangles real/theory",triInx,maxtriangles*len(self.fitFrames['lights'])
		self.result=result

	def match(self):
		triErr=0.001
		result=self.result
		dt=np.dtype([('frame',int),('err',float),('refpoints',np.float32,(3,2)),('points',np.float32,(3,2))])
		matchedTriangles=np.zeros((1,),dtype=dt)
		matchedBuffer=np.zeros((1,),dtype=dt)
		matchCount=0
		for k,light in enumerate(self.fitFrames['lights']):
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

	def homografy(self):
		matchedTriangles=self.matchedTriangles
		homo={}
		for k,light in enumerate(self.fitFrames['lights']):
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

	def stack(self,band,combine='median'):
		xdeltaMax=0
		xdeltaMin=0
		ydeltaMax=0
		ydeltaMin=0
		fitsList=[]
		for k,light in enumerate(self.fitFrames['lights']):
			if k==0:
				fitsList.append(light)
				continue	
			print "Frame",light,k	
			homo=self.homo
			frame=fitsMaths.fitMaths(light)
			x_=homo[k]['x']	
			y_=homo[k]['y']
			print "Shifting:",x_,y_
			frame.hdulist[0].data=shift(frame.hdulist[0].data,(-y_,-x_))
			shiftedlight=light.replace('IMG','_IMG')
			frame.save(shiftedlight)
			fitsList.append(shiftedlight)
		if not os.path.exists(self.cfg['resultdir']):
			os.makedirs(self.cfg['resultdir'])
		outfile=self.cfg['resultdir']+"/output."+band+".fit"
		Master=fitsMaths.combineFits(fitsList,combine=combine)
		Master.save(outfile)
		return outfile

	def distance(self,p0,p1):
		return np.sqrt((p1[0]-p0[0])**2+(p1[1]-p0[1])**2)

	def doRGB(self,combine='median',baseband='Gi1'):
		bands=['Ri','Gi1','Gi2','Bi']
		self.BaseBand=baseband
		try:
			del self.lightFitsBase
		except:
			pass
		bands.remove(baseband)
		print "BASE BAND:",baseband
		print "Other bands:",bands
		if self.num['lightsBase']>1:
			self.rankFrames(self.BaseBand)
			self.getTriangles()
			self.match()
			self.homografy()
		filename=self.stack(baseband,combine=combine)
		outfiles={baseband:filename}
		for B in bands:
			filename=self.stack(B,combine=combine)
			outfiles[B]=filename
		'''combine Gi1 and Gi2 '''
		Gi=fitsMaths.combineFits((outfiles['Gi1'],outfiles['Gi2']),combine='median')
		filename=self.cfg['resultdir']+"/output.Gi.fit"
		Gi.save(filename)
		outfiles.pop("Gi1", None)
		outfiles.pop("Gi2", None)
		outfiles['Gi']=filename
		return outfiles

	def doLuminance(self,combine='median'):
		self.BaseBand='P'
		try:
			del self.lightFitsBase
		except:
			pass

		print "Luminance band:",self.BaseBand
		if self.num['lightsBase']>1:
			self.rankFrames(self.BaseBand)
			self.getTriangles()
			self.match()
			self.homografy()
		filename=self.stack(self.BaseBand,combine=combine)
		outfiles={self.BaseBand:filename}
		return outfiles


if __name__ == '__main__':
	'''

	'''
	co=registrarTriangle()
#	RGBfiles=co.doRGB(combine='max')
#	RGBfiles={'Bi': './OUTPUT/output.Bi.fit', 'Gi': './OUTPUT/output.Ri.fit', 'Ri': './OUTPUT/output.Gi.fit'}
#	fBaseComposer.RGBcomposer(RGBfiles,gamma=1)
	Lfiles=co.doLuminance(combine='median')
#	Lfiles={'u':'./OUTPUT/output.u.fit'}
#	fBaseComposer.RGBcomposer(Lfiles,gamma=1)








	
