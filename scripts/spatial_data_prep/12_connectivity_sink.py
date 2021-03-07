# calculate the amount of recruits each meadow receives from MPAs.
# This can be interpreted in 2 ways:
#   (1) An important sink/link in the network - a seagrass patch that is 
#   unprotected and is receiving a high amount of recruits from MPAs
#   (2) An important gap to fill - a meadow that is located in a place that is 
#   not receiving recruits and could therefore

# create 'sink_from_mpa_count' attribute

# a significant challenge: dealing with the different coastline datasets I used
# in the different chapters

# For the sink metric, I will include particles that came from US MPAs. However,
# for the source metric, I will only consider connections to Canadian coastline.

import arcpy
import os


root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'connectivity_sink.gdb'
arcpy.env.workspace = os.path.join(root, gdb)

# mpa connectivity results
mpa_dest_gdb = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\cluster_results\scripts\DEST_RAST.gdb'
mpa_dest_pts = 'clip_destpts_{}_pld{}' # no retention and removes for mortality,
# then spatially selected to be over coast, mpa, coast buff30, or bathy 30.
dates = ['1101', '1105', '1108', '1401', '1405', '1408', '1701', '1705', '1708']
plds = ['1', '60']

# coastline used for seagrass connectivity
coastline = 'main_seagrass.gdb/coastline_bc_ak_wa_or_cleaned_less10000'
# coastline for mpa connectivity
coastline_mpa = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\spatial\Coastline\coastline.gdb\landmask_FINAL'

# seagrass retraced to coastline
sg_retrace = 'main_seagrass.gdb/sg_101_retrace'

# Salish Sea Canada poly
salishsea_clippoly = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial\population.gdb\clip_rast_poly'


#############################################
# select destination points from mpa connectivity chapter

# issue with dest points is that there are points that are selected that are 
# over 30 m bathy, or because the coasts don't line up they are in a gap between
# the meadow and the coastline farther inland.
# First, clip to salish sea poly
# Then buffer mpa landmask by 30m (just to catch any that "strand" just outside
# of the landmask.
# Then merge: seagrass, seagrass coastline, and buffered mpa landmask
# Then clip points to this poly.
# NOTE: I recognize that this is not perfect. Assumptions are made when clipping
# over both coastlines. Best I can do.

for pld in plds:
    for date in dates:
        fc = os.path.join(mpa_dest_gdb, mpa_dest_pts.format(date, pld))
        arcpy.Clip_analysis(fc, salishsea_clippoly, mpa_dest_pts.format(date, pld))

for pld in plds:
    fcs = arcpy.ListFeatureClasses('*pld' + pld)
    arcpy.Merge_management(fcs, f'dest_pts_pld{pld}')

fcs = arcpy.ListFeatureClasses('clip*')
for fc in fcs:
    arcpy.Delete_management(fc)

arcpy.Buffer_analysis(coastline_mpa, 'coastline_mpa_buff30', 30)
arcpy.Merge_management(
    ['coastline_mpa_buff30', 
    os.path.join(root, coastline), 
    os.path.join(root, sg_retrace)], 
    'merge_coasts_sg')

fcs = arcpy.ListFeatureClasses('dest*')
for fc in fcs: 
    arcpy.Clip_analysis(fc, 'merge_coasts_sg', fc + '_clip')



##############################################
# do NEAR analysis
# snap each point the nearest point of the coastline used in the seagrass study
# Since seagrass meadows are snapped to this coast, the only way to properly get
# them to line up for a spatial join is to have them on this coastline.
# Otherwise I would have to buffer the meadows with variable uncertain results.

arcpy.PolygonToLine_management(os.path.join(root, coastline), 'coastline_polytoline')
for pld in plds:
    fc = f'dest_pts_pld{pld}_clip'
    arcpy.Near_analysis(fc, 'coastline_polytoline', location='LOCATION')
    arcpy.TableToTable_conversion(fc, arcpy.env.workspace, fc + '_neartbl')
    arcpy.MakeXYEventLayer_management(
        fc+'_neartbl', 
        'NEAR_X', 
        'NEAR_Y', 
        'tmplyr',
        3005)
    arcpy.CopyFeatures_management('tmplyr', fc+'_neartbl_pts')
    arcpy.Delete_management('tmplyr')


##############################################
# associate with seagrass
for pld in plds:
    fc = f'dest_pts_pld{pld}_clip_neartbl_pts'
    arcpy.SpatialJoin_analysis(
        os.path.join(root, sg_retrace),
        fc, 
        f'sg_pld{pld}_01_spatialjoin', 
        'JOIN_ONE_TO_MANY', 
        'KEEP_ALL', 
        match_option='INTERSECT',
        search_radius=25
    )

# there might be some pts that were right on the border of their home seagrass
# meadow that made it through the selection. Get rid of these.
for pld in plds:
    fc = f'sg_pld{pld}_01_spatialjoin'
    sel = arcpy.SelectLayerByAttribute_management(
        fc,
        'NEW_SELECTION',
        'uID <> uID_part'
    )
    arcpy.CopyFeatures_management(sel, f'sg_pld{pld}_02_selattr')


##############################################
# get count of points per meadow and clean up

for pld in plds:
    fc = f'sg_pld{pld}_02_selattr'
    arcpy.AddField_management(fc, 'sink_particles', 'LONG')
    with arcpy.da.UpdateCursor(fc, ['sink_particles']) as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)
    arcpy.Frequency_analysis(fc, f'sg_pld{pld}_03_freq', ['uID'], ['sink_particles'])

# some these datasets are large
# delete most of them. Most of these functions run quickly anyways.
fcs = arcpy.ListFeatureClasses('dest_pts*')
for fc in fcs:
    if not fc.endswith('pts'):
        arcpy.Delete_management(fc)
tbls = arcpy.ListTables('dest*')
for t in tbls:
    if not t.startswith('sg'):
        arcpy.Delete_management(t)
arcpy.Delete_management('coastline_mpa_buff30')
arcpy.Delete_management('coastline_polytoline')
arcpy.Delete_management('merge_coasts_sg')
fcs = arcpy.ListFeatureClasses('sg_pld*')
for fc in fcs:
    arcpy.Delete_management(fc)

# frequency table 'sink_particles' is the result to join to main seagrass dataset