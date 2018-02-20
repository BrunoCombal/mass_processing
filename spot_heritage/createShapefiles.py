import os
import fnmatch
import xml.etree.ElementTree as ET
import os.path
import sys
import re
import shutil
import ogr, osr


inDir='//ies.jrc.it/H03/FOROBS/optical1/afr/spot/spot_afd/Pivot_2010/Ortho'
#inDir='//ies.jrc.it/H03/FOROBS/optical1/afr/spot/spot_afd/Pivot_2015/Ortho'
outDir='E:/tmp/exportSpot'
shpfile = os.path.join(outDir, 'refGrid2010_wgs84.shp')
outSpatialRef = osr.SpatialReference()
outSpatialRef.ImportFromEPSG(4326)
#shpfile = os.path.join(outDir, 'refGrid2015_UTM_32N.shp')
driver = ogr.GetDriverByName('ESRI Shapefile')
if os.path.exists(shpfile):
	driver.DeleteDataSource(shpfile)
outDS = driver.CreateDataSource(shpfile)
dateField=ogr.FieldDefn("date", ogr.OFTString)
dateField.SetWidth(10)
idField=ogr.FieldDefn("id", ogr.OFTString)
idField.SetWidth(20)
missionField=ogr.FieldDefn("mission", ogr.OFTString)
missionField.SetWidth(10)
outLayer = outDS.CreateLayer("footprint", outSpatialRef, geom_type=ogr.wkbPolygon)
outLayer.CreateField(dateField)
outLayer.CreateField(idField)
outLayer.CreateField(missionField)
featureDfn = outLayer.GetLayerDefn()

renameList={}

for root, dirnames, filenames in os.walk(inDir):
	if re.match('.*duplicates.*', root) is None: # we skip directory duplicates
		for filename in fnmatch.filter(filenames, 'IMAGERY.TIF'):
			xmlFile = os.path.join(root, 'METADATA.DIM')
			tree = ET.parse(xmlFile)
			rootXML = tree.getroot() 

			thisDate = rootXML.findall('.//IMAGING_DATE')[0].text # is a string
			lon = rootXML.findall('.//Dataset_Frame/Vertex/FRAME_LON')
			lat = rootXML.findall('.//Dataset_Frame/Vertex/FRAME_LAT')
			#lon = rootXML.findall('.//Dataset_Frame/Vertex/FRAME_X')
			#lat = rootXML.findall('.//Dataset_Frame/Vertex/FRAME_Y')

			if len(lon) != 4:
				print len(lon), root
				#print [ii.text for ii in lon]
				#print [ii.text for ii in lat]
				#sys.exit()

			ring = ogr.Geometry(ogr.wkbLinearRing)
			for ii in range(len(lon)):
				ring.AddPoint( float(lon[ii].text), float(lat[ii].text))
			ring.AddPoint( float(lon[0].text), float(lat[0].text) ) # to close the polygon

			poly = ogr.Geometry(ogr.wkbPolygon)
			poly.AddGeometry(ring)
			thisMission = rootXML.findall('.//MISSION_INDEX')[0].text
			thisSourceID = rootXML.findall('.//SOURCE_ID')[0].text

			poly = ogr.Geometry(ogr.wkbPolygon)
			poly.AddGeometry(ring)
			feature = ogr.Feature(featureDfn)
			feature.SetGeometry(poly)
			feature.SetField("date", thisDate)
			feature.SetField("id", thisSourceID)
			feature.SetField("mission", thisMission)
			outLayer.CreateFeature(feature)
			feature = None

			#newName = 'SPOT_{}_{}_{}_{}.tif'.format(thisMission, thisDate, thisULX, thisULY)
			newName = 'SPOT_{}_{}_{}.tif'.format(thisMission, thisDate, thisSourceID)
			print os.path.join(root, filename), ' --> ', os.path.join(outDir,newName)
			#shutil.copyfile(os.path.join(root, filename), os.path.join(outDir,newName))

outDS = None
# end of code