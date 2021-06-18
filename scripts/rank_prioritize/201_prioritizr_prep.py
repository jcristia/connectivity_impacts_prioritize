# prepare data inputs for prioritizr
# see Impacts\scripts\prioritizr_seagrass\prioritizr_scenarios.xlsx

import arcpy
import os

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'prioritizr.gdb'
arcpy.env.workspace = os.path.join(root, gdb)
sg = os.path.join(root, 'main_seagrass.gdb/sg_5_join_norm')

# copy to prioritizr gdb
arcpy.CopyFeatures_management(sg, 'sg_01_copy')

# add area attribute and calculate in km2 (prioritizr doesn't like large numbers)
arcpy.AddField_management('sg_01_copy', 'area', 'FLOAT')
with arcpy.da.UpdateCursor('sg_01_copy', ['Shape_Area', 'area']) as cursor:
    for row in cursor:
        row[1] = row[0] / 1000000.0
        cursor.updateRow(row)

# convert to points
arcpy.FeatureToPoint_management('sg_01_copy', 'sg_02_pt', 'INSIDE')

# Add fields
arcpy.AddFields_management(
    'sg_02_pt',
    [
        ['id', 'SHORT', 'id'],
        ['cost1', 'DOUBLE', 'cost1'],
        ['cost2', 'LONG', 'cost2'],
        ['locked_in', 'TEXT', 'locked_in', 50],
        ['locked_out', 'TEXT', 'locked_out', 50],
        ['dummy_con', 'SHORT', 'dummy_con'],
        ['area_scaled', 'DOUBLE', 'area_scaled']
    ]
)

# Calc fields:

# id = uID
# cost1 = area
# cost2 = 1
# dummy_con = 1
fields = [
    'uID', 'id',
    'area', 'cost1', 'cost2',
    'dummy_con'
    ]
with arcpy.da.UpdateCursor('sg_02_pt', fields) as cursor:
    for row in cursor:
        row[1] = row[0]
        row[3] = row[2]
        row[4] = 1
        row[5] = 1
        cursor.updateRow(row)

# Locked in/out:
# I initially just added TRUE if anything overlapped with an MPA:
# locked_in = TRUE if mpa overlap > 0
# locked_out = TRUE if mpa overlap > 0
# However...
# Some large meadows overlap just a small bit with an mpa. I wouldn't want to
# exclude these. However, I shouldn't do it just by % overlap because some very
# small meadows only overlap a bit with an mpa, but given their size and the 
# mismatch in meadow/mpa boundaries, I would still want to lock these ones out.
# Therefore, determine a combination overlap/total area criteria to
# exclude/include meadows.
# Through some trial and error I concluded: overlap of 20% and meadows greater
# than 0.5 km2
fields = [
    'percent_mpaoverlap', 'area',
    'locked_in', 'locked_out',
    ]
with arcpy.da.UpdateCursor('sg_02_pt', fields) as cursor:
    for row in cursor:
        if row[0] > 0:
            row[2] = 'TRUE'
            row[3] = 'TRUE'
        else:
            row[2] = 'FALSE'
            row[3] = 'FALSE'
        if row[0] < 20 and row[0] > 0 and row[1] > 0.5:
            row[2] = 'FALSE'
            row[3] = 'FALSE'
        cursor.updateRow(row)

# scale area to 0 to 1
search_cursor = arcpy.da.SearchCursor('sg_02_pt', 'area')
max_val = max(search_cursor)[0]
search_cursor.reset()
min_val = min(search_cursor)[0]
with arcpy.da.UpdateCursor('sg_02_pt', ['area', 'area_scaled']) as cursor:
    for row in cursor:
        row[1] = (row[0] - min_val) / (max_val - min_val)
        cursor.updateRow(row)

# Delete fields:
# uID, area_clipmpa, percent_mpaoverlap, ORIG_FID
arcpy.DeleteField_management('sg_02_pt', ['uID', 'area_clipmpa', 'percent_mpaoverlap', 'ORIG_FID'])




