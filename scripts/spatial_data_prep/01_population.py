# assign population in a watershed to each seagrass meadow


import arcpy
from arcpy.sa import *
import os

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
outgdb = 'population.gdb'
watersheds = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\1Data_BASE\BASE\BASE_hydrology.gdb\WHSE_BASEMAPPING_FWA_ASSESSMENT_WATERSHEDS_POLY'
sg = 'main_seagrass.gdb/sg_101_retrace'
pop_rast = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\1Data_BASE\Population\gpw-v4-population-count-rev11_2020_30_sec_tif\gpw_v4_population_count_rev11_2020_30_sec.tif'
arcpy.env.workspace = os.path.join(root, outgdb)


# copy seagrass to population gdb
# these are the polys that were retraced to align with the coastline
sg_retraced = os.path.join(root, sg)
arcpy.CopyFeatures_management(sg_retraced, 'sg_101_retraced')

# buffer by 100m to remove any slivers and to create overlap with watershed
# so that I can do a spatial select. It will also create overlap for meadows
# that are more offshore.
arcpy.Buffer_analysis('sg_101_retraced', 'sg_102_buff100', 100)

# Copy
# and then do a spatial select with watersheds to see which meadows are not
# overlapping. Then, !!!MANUALLY!!! extend these to the coast. Create a bit of overlap
# for a spatial select.
arcpy.CopyFeatures_management('sg_102_buff100', 'sg_103_extend')
# there were 6 features that overlapped, but I also edited additional features
# near Nanaimo (uid 569, 568, 601, 603, 605). There overlap with parts of watersheds was weird.
# I want them all to overlap the same watersheds.


# Spatially select the watersheds that intersect with the seagrass meadows
arcpy.MultipartToSinglepart_management(watersheds, 'watersheds_multisingle')
watershed_sel = arcpy.SelectLayerByLocation_management('watersheds_multisingle', 'INTERSECT', 'sg_103_extend')
arcpy.CopyFeatures_management(watershed_sel, 'watersheds_01_intersect')
arcpy.Delete_management('watersheds_multisingle')
# there isn't a clear unique ID in the dataset. Add one.
arcpy.AddField_management('watersheds_01_intersect', 'jc_ID', 'SHORT')
with arcpy.da.UpdateCursor('watersheds_01_intersect', ['OBJECTID_1', 'jc_ID']) as cursor: # note that objectdid is actually 'OBJECTID_1'
    for row in cursor:
        row[1] = row[0]
        cursor.updateRow(row)


# Population
# I can't figure out how to select raster cells if the polygons don't overlap the
# cell centers. All the tools are set up this way and there isn't an option to
# do anything different.
# This isn't a big deal for bigger watersheds, but for islands and narrow areas,
# there are many cells that are not selected.
# You also cannot just turn the cells to polygons. Similar values get combined
# and create larger polygons and there is no way to prevent this.
# So... I may have to do this in a round about way.

arcpy.CopyRaster_management(pop_rast, 'population_01')
outRast = ExtractByMask('population_01', 'clip_rast_poly')
outRast.save('population_02_clip')

# https://support.esri.com/en/technical-article/000012696
arcpy.RasterToPoint_conversion('population_02_clip', 'population_03_pts')
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)
arcpy.CreateFishnet_management(
    'population_04_fishnet',
    '-126.308333333333 48.1999999999999',
    '-126.308333333333 58.1999999999999',
    None, None,
    290, 478,
    '-122.325 50.6166666666666',
    'LABELS',
    None,
    'POLYGON')
arcpy.FeatureToPolygon_management(
    'population_04_fishnet',
    'population_05_values',
    label_features='population_03_pts')

arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3005)


# spatial join
arcpy.SpatialJoin_analysis(
    'watersheds_01_intersect', 
    'population_05_values', 
    'watersheds_02_sjoin',
    'JOIN_ONE_TO_MANY',
    'KEEP_ALL',
    match_option='INTERSECT')


# frequency
arcpy.Frequency_analysis('watersheds_02_sjoin', 'watersheds_03_frequency', ['jc_ID'], ['grid_code'])


# spatial join, watersheds to seagrass
arcpy.SpatialJoin_analysis(
    'sg_103_extend',
    'watersheds_01_intersect',
    'sg_104_sjoin',
    'JOIN_ONE_TO_MANY',
    'KEEP_ALL',
    match_option='INTERSECT'
)

# join frequency table to seagrass
sg_joined_table = arcpy.AddJoin_management('sg_104_sjoin', 'jc_ID', 'watersheds_03_frequency', 'jc_ID')
# frequency
arcpy.Frequency_analysis(sg_joined_table, 'sg_105_freq', ['uID'], ['grid_code'])
# this is the end product. From this I have the uID of the seagrass meadow,
# the population of all the watersheds that touch that seagrass meadow
# and there is also a frequency field that shows how many touch that meadow