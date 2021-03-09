
# calculate the amount of recruits that move from seagrass meadows to 
# unprotected areas of the coast

# This can tell us:
#   (2) if it acts as a source to unprotected areas of the coast that are not
#       seeded by the current network of MPAs

# This metric should be interpretted as the difference in recruits that this 
# seagrass meadow could contribute to a part of unprotected coast.
# So if an area already has a lot of recruits from MPAs, and even if a seagrass
# meadow also sends a lot of recruits there, unless it is sending a substantial
# additional amount more then it won't show up as significant.
# This must be interpreted correctly:
# it is about identifying areas where recruitment from seagrass can make a
# significant difference. We want to see the areas that didn't have a lot of
# recruitment before, but now does.
# AREAS WHERE SEAGRASS CAN MAKE AN OUTSIZE DIFFERENCE IF ADDED TO THE NETWORK.
# However, that means that if we look at an area that receives the same recruits
# from each, then it will look like seagrass doesn't contribute anything to that
# area. This is not necessarily the case.

'''
One big assumption of this is that all particles have the same weight of
influence. The number of particles released was done by area of origin patch,
however this ratio (particles/area) was different between the mpa and seagrass 
studies.

seagrass:
total_area = 1194942034
total_particles = 3798754
mpas:
total_area = 6,420,713,141
total_particles = 2950619

I drastically reduced the amount of particles in the mpa study when compared
to the seagrass study. Therefore, 1 particle from the mpa study has more 
"influence" than a particle from the seagrass study (i.e. it represents ~7
seagrass particles arriving to the same spot).
However, that ratio changes since for the mpa study the ratio with area changed
so that with smaller meadows the ratio would probably be flipped. To add any kind
of correction, I would have to know the origin of the mpa particles, which means
a lot of that would have to be ran again. Not gonna happen.
So perhaps given the changing ratio, on average it is actually comparable.
This will just have to be one of the assumptions of the paper.

How I will frame this:
This source metric is designed to just give an indication of where a seagrass
meadow could be filling a gap. I will be standardizing the numbers between 0 and 1
and I will see it as just relative - as a comparison between meadows. Also, since
it is an individual based model. The arrival of any particle is still significant
and informative regardless of the amount released, especially in the Salish Sea.
Given the contrained nature of it, paths are more deterministic (not as much
room and time to vary).
'''

# Attributes:
# 	source_to_gap_count_pld01
# 	source_to_gap_count_pld60

# For the sink metric, I will include particles that came from US MPAs. However,
# for the source metric, I will only consider connections to Canadian coastline.


# OVERALL WITH ALL THESE METRICS:
# This is not a perfect solution. This is the best I can do. It will simply
# need to be viewed as an estimation with some error involved.




import arcpy
from arcpy.sa import *
import os
import pandas as pd
import numpy as np


root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'connectivity_gapfill.gdb'
arcpy.env.workspace = os.path.join(root, gdb)

# These are the points created in connectivity_source.py. It is the seagrass
# destination points with the points snapped to the mpa coastline. Most points
# that overlap with mpas are removed, but some may remain after snapping.
dest_pts_adjusted = os.path.join(root, 'connectivity_source.gdb/destpts_13_pld{}_remove')

plds = [1, 60]

snapras = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\cluster_results\scripts\DEST_RAST.gdb\recruit_count_ALL_1_rmMPAs'
arcpy.env.snapRaster = snapras
arcpy.env.cellSize = snapras

mpa_buff = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\spatial\MPA\mpas_shp_release\mpas.gdb\MB06_mpa_buff_FINAL'

# mpa recruit rasters
mpa_recruit_ras = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\cluster_results\scripts\DEST_RAST.gdb\recruit_count_ALL_{}_rmMPAs'


def rasterizeMpaBuff(mpa_buff, outmpa_ras):
    """
    Rasterize the mpas to use for removing particles. We are only interested
    in recruitment to unprotected areas.
    """
    mpa_buff_out = os.path.basename(mpa_buff)
    arcpy.CopyFeatures_management(mpa_buff, mpa_buff_out)
    arcpy.AddField_management(mpa_buff_out, 'priority', 'SHORT')
    with arcpy.da.UpdateCursor(mpa_buff_out, ['priority']) as cursor:
        for row in cursor:
            row[0]=1
            cursor.updateRow(row)
    arcpy.PolygonToRaster_conversion(
        mpa_buff_out, 
        'OBJECTID', 
        mpa_buff_out + '_ras', 
        'MAXIMUM_AREA', 
        priority_field='priority')
    # its super important to have a priority field and the conversion set to 
    # maximum area or else it won't give a cell a value unless the polygon 
    # crosses the cell center

    # give the cells a value of 0 where there is an mpa and a value of 1 elsewhere:
    outCon = Con(mpa_buff_out + '_ras', 0, 1, "Value > 0")
    outisnull = IsNull(outCon)
    outisnull.save(outmpa_ras)


def pointsToRaster(pld, uid, fc, destras):
    """
    Convert destination points to raster.
    """
    arcpy.MakeFeatureLayer_management(fc, 'tmp_lyr', f'uID = {uid}')
    arcpy.PointToRaster_conversion('tmp_lyr', '', destras, 'COUNT', cellsize=1000)
    arcpy.Delete_management('tmp_lyr')


def removeWhereMpa(pld, uid, destras, outmparas):
    """
    Remove cells from the destination raster where there is an MPA.
    """
    # use the set null tool
    # If mparast is zero then the output raster will be null there, but where it
    # is not then it will use the values from recruitras
    outras = SetNull(outmparas, destras, 'Value = 0')
    outras.save(destras + '_rmMPAs')
    # delete first raster
    arcpy.Delete_management(destras)


def calcGapFillDifference(mpa_recruit_ras_pld):
    """
    Subtract the mpa points raster from the seagrass raster.
    """

    sg_ras = destras + '_rmMPAs'

    # subtract
    # to do subtract, the mpa recruit raster needs the null values turned to zero
    outras_mpa = Con(IsNull(mpa_recruit_ras_pld),0,mpa_recruit_ras_pld)
    outras = Raster(sg_ras) - outras_mpa
    outras.save(sg_ras + '_diff')

    # delete previous raster
    arcpy.Delete_management(sg_ras)


def gapFillTotal():
    """
    Add up all raster cell values and assign to meadow.
    """
    sg_ras = destras + '_rmMPAs_diff'

    # rasters have an output table that you can use a normal SearchCursor with
    total = 0
    with arcpy.da.SearchCursor(sg_ras, ['Value']) as cursor:
        for row in cursor:
            if row[0] > 0:
                total += row[0]
    return total



#######################################################################

outmparas = os.path.basename(mpa_buff) + '_ras_isnull'
rasterizeMpaBuff(mpa_buff, outmparas)

for pld in plds:
    fc = dest_pts_adjusted.format(str(pld))
    uIDs = list(set([i[0] for i in arcpy.da.SearchCursor(fc, 'uID')]))
    mpa_recruit_ras_pld = mpa_recruit_ras.format(str(pld))
    gap_dict = {'uID':[], 'gapTotal':[]}
    for uid in uIDs:
        destras = f'destrast_pld{str(pld)}_{str(int(uid))}'
        pointsToRaster(pld, uid, fc, destras)
        removeWhereMpa(pld, uid, destras, outmparas)
        calcGapFillDifference(mpa_recruit_ras_pld)
        total = gapFillTotal()
        gap_dict['uID'].append(uid)
        gap_dict['gapTotal'].append(total)
    df = pd.DataFrame(gap_dict)
    x = np.array(np.rec.fromrecords(df.values))
    names = df.dtypes.index.tolist()
    x.dtype.names = tuple(names)
    arcpy.da.NumPyArrayToTable(x, os.path.join(root, 'connectivity_gapfill_results.gdb', f'sg_01_pld{str(pld)}_gaptotal'))
       
# These tables by pld will be what I used for the attributes in the main
# seagrass dataset.