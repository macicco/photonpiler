#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import fitsMaths
import glob
import os,commands
import pyfits
import time
import numpy as np


class Composer():

	def __init__(self,path):
		self.scriptpath, self.scriptname = os.path.split(os.path.abspath(__file__))
		print "Script path:",self.scriptpath
		self.path=path
		self.lightspath=path+"/SCIENCE"
		self.darkspath=path+"/DARKS"
		self.flatspath=path+"/FLATS"
		self.outdir=path+"/OUTPUT"
		if not os.path.exists(self.outdir):
			os.mkdir(self.outdir) 
		self.lightRaws=self.searchRawFiles(self.lightspath)
		self.lightFits=self.rawtran(self.lightRaws)
		self.NumLights=len(self.lightFits)
		if os.path.exists(self.darkspath):
			self.darkRaws=self.searchRawFiles(self.darkspath)
			self.darkFits=self.rawtran(self.darkRaws)
			self.NumDarks=len(self.darkFits)
			print "=========== DARK FRAMES =============="
			print "Path:", self.darkspath
			print "Light frames found:",self.NumDarks
			print self.darkRaws
			print self.darkFits
			dark=self.MasterDark()
			dark.save(self.outdir+'/masterdark.fit')
		else:
			print "NO DARKS"
		
		if os.path.exists(self.flatspath):
			self.flatRaws=self.searchRawFiles(self.flatspath)
			self.flatFits=self.rawtran(self.flatRaws)
			self.NumFlats=len(self.flatFits)
			print "=========== FLAT FRAMES =============="
			print "Path:", self.flatspath
			print "Light frames found:",self.NumFlats
			print self.flatRaws
			print self.flatFits
			flat=self.MasterFlat()
			flat.save(self.outdir+'/masterflat.fit')
		else:
			print "NO FLATS"


		print "Processing directory:",path
		print "=========== LIGHT FRAMES =============="
		print "Path:", self.lightspath
		print "Light frames found:",self.NumLights
		print self.lightRaws
		print self.lightFits
		print "=========== OUTPUT =============="
		print "Path:", self.outdir




	def searchRawFiles(self,path):
		l=[]
		for file in os.listdir(path):
		    if file.endswith(".CR2"):
			l.append(path+"/"+file)
		return l

	def rawtran(self,raws):
		l=[]
		for raw in raws:
			outfile=self.outdir+"/"+os.path.basename(raw).replace('CR2','fit')
			if not os.path.exists(outfile):
				print "rawtran-ting:",outfile
				strCmd= 'rawtran -c u -B -32 -o '+outfile+ " " + raw
				print strCmd
				res=commands.getoutput(strCmd)
				print res
			else:
				print "Already exist:",outfile
			l.append(outfile)
		return l

	def catalog(self):
		for light in self.lightFits:
			self.sex(light)

	def match(self):
		seeing=60

		for i,light in enumerate(self.lightFits):
			if i==0:
				cat1=self.lightFits[i].replace('.fit','.cat')				
			else:
				cat2=self.lightFits[i].replace('.fit','.cat')
				stiltsStr="stilts tmatch2  fixcols=none in1="+cat1+ " in2="+cat2+" \
					matcher=sky params="+str(seeing)+" \
			       		values1=\"X_IMAGE Y_IMAGE\" \
       					values2=\"X_IMAGE Y_IMAGE\" \
				   	join=1and1  \
					out="+name+".matched.cat  ofmt=fits-basic"
				print stiltsStr
				res=commands.getoutput(stiltsStr)
				print res
	def stack(self):
		pass


	def sex(self,fit):
		name=fit.replace('.fit','.cat')
		if not os.path.exists(name):
			#outfile=self.outdir+"/"+os.path.basename(fit).replace('fit','cat')
			sexStr="sex "+fit+" -c "+self.scriptpath+"/registra.sex -CATALOG_NAME "+name+ \
			" -PARAMETERS_NAME "+self.scriptpath+"/registra.param"+ \
			" -FILTER_NAME "+self.scriptpath+"/registra.conv"
			print "EXECUTING:",sexStr
			res=commands.getoutput(sexStr)
			print res
		
		hdulist=pyfits.open(name)
		data=hdulist[1].data
		return data

	def MasterFlat(self):
		return (1./self.NumFlats)*self.Sum(self.flatFits)

	def MasterDark(self):
		return (1./self.NumDarks)*self.Sum(self.darkFits)


	def lightSum(self):
		return self.Sum(self.lightFits)

	def Sum(self,fits):

		for i,fit in enumerate(fits):
			if i==0:
				Master=fitsMaths.fitMaths(fit)
				print "init sum:",fit
			else:
				Master=fitsMaths.fitMaths(fit)+Master
				print "+",fit
		return Master

class triangleComposer(Composer):
	def getTriangles(self):
		numstars=10
		maxtriangles=numstars*(numstars-1)*(numstars-2)/6
		dt=np.dtype([('frame',int),('v0',int),('v1',int),('v2',int),('sA',float),('sB',float),('points',np.float32,(3,2))])
		result=np.zeros((maxtriangles*len(self.lightFits),),dtype=dt)
		triInx=0
		for k,light in enumerate(self.lightFits):
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
		print "Triangles real/theory",triInx,maxtriangles*len(self.lightFits)
		self.result=result

	def match(self):
		triErr=0.0001
		result=self.result
		dt=np.dtype([('frame',int),('err',float),('refpoints',np.float32,(3,2)),('points',np.float32,(3,2))])
		matchedTriangles=np.zeros((1,),dtype=dt)
		matchedBuffer=np.zeros((1,),dtype=dt)
		matchCount=0
		for k,light in enumerate(self.lightFits):
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
						print np.average((pp-p),axis=0)
						matchCount=matchCount+1
		print matchCount
		#print matchedTriangles
		return matchedTriangles

	def homografy(self):
		pass

	def distance(self,p0,p1):
		return np.sqrt((p1[0]-p0[0])**2+(p1[1]-p0[1])**2)

class resolvComposer(Composer):

	def astrometry(self):
		self.solve_fits=map(lambda x:x.replace('.fit','.new'),self.lightFits)
		for i,fit in enumerate(self.lightFits):
			astrometryStr="solve-field  "+fit +" -z 4 --overwrite -p"
			print "EXECUTING:\n",astrometryStr
			res=commands.getoutput(astrometryStr)
			print res


	def catalog(self):
		for light in self.solve_fits:
			self.sex(light)	

	def scamp(self):
		cats=map(lambda x:x.replace('.fit','.cat'),self.lightFits)
		lista=" "
		for i,cat in enumerate(cats):
			lista=lista+" "+cat
		print "SCAMP catalogs:\n",cats
		swarpStr="scamp -c "+self.scriptpath+"/scamp.conf "+lista 
		print "EXECUTING:\n",swarpStr
		res=commands.getoutput(swarpStr)
		print res

	def swarp(self):
		lista=" "
		for i,fit in enumerate(self.lightFits):
			lista=lista+" "+fit
		path=cfg['dir_swarp_base']+'/'+self.getToday()+'/swarp'
		if not os.path.exists( path):
    			os.makedirs(path)
		swarpStr="swarp -c "+cfg["swarpcfg"]+lista+ " -IMAGEOUT_NAME "+path+"/"+self.frame+".fit "+\
		" -WEIGHTOUT_NAME  "+path+"/" +self.frame+".weight.fit "
		print "EXECUTING:\n",swarpStr
		res=commands.getoutput(swarpStr)
		print res
		return path+"/"+self.frame+".fit"


if __name__ == '__main__':
	co=triangleComposer('.')
	co.getTriangles()
	co.match()
	'''
	l=co.lightSum()
	l.save('kk.fit')

	'''

	
