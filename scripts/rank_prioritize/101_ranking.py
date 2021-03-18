# simply ranking scheme of impacts and connectivity metrics

import arcpy
import os

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'main_seagrass.gdb'
sg = 'sg_6_norm'
arcpy.env.workspace = os.path.join(root, gdb)


arcpy.CopyFeatures_management(sg, 'sg_7_ranking')

# add fields for everything I'll do in this script
arcpy.AddFields_management(
    'sg_7_ranking',
    [
        ['tot_imp', 'DOUBLE', 'tot_imp'],
        ['tot_con', 'DOUBLE', 'tot_con'],
        ['tot_imp_norm', 'DOUBLE', 'tot_imp_norm'],
        ['tot_con_norm', 'DOUBLE', 'tot_con_norm'],
        ['naturalness', 'DOUBLE', 'naturalness'],
        ['ranking_nonorm', 'DOUBLE', 'ranking_nonorm'],
        ['ranking_overall', 'DOUBLE', 'ranking_overall'],
    ]
)

# add impacts and connectivity metrics separately
fields = ['popn', 'ow_perc', 'smodperc', 'agricult', 'cutblock', 'gcrab', 'reg_sink', 'reg_sour', 'tot_imp']
with arcpy.da.UpdateCursor('sg_7_ranking', fields) as cursor:
    for row in cursor:
        row[8] = row[0] + row[1] + row[2] + row[3] + row[4] + row[5] + row[6] + row[7]
        cursor.updateRow(row)
fields = ['dPCpld01', 'dPCpld60', 'sink_01', 'sink_60', 'source01', 'source60', 'gpfill01', 'gpfill60', 'tot_con']
with arcpy.da.UpdateCursor('sg_7_ranking', fields) as cursor:
    for row in cursor:
        row[8] = row[0] + row[1] + row[2] + row[3] + row[4] + row[5] + row[6] + row[7]
        cursor.updateRow(row)

# normalize
search_cursor = [row[0] for row in arcpy.da.SearchCursor('sg_7_ranking', ['tot_imp'])]
maxval = max(search_cursor)
minval = min(search_cursor)
with arcpy.da.UpdateCursor('sg_7_ranking', ['tot_imp', 'tot_imp_norm']) as cursor:
    for row in cursor:
        row[1] = (row[0] - minval) / (maxval - minval)
        cursor.updateRow(row)
search_cursor = [row[0] for row in arcpy.da.SearchCursor('sg_7_ranking', ['tot_con'])]
maxval = max(search_cursor)
minval = min(search_cursor)
with arcpy.da.UpdateCursor('sg_7_ranking', ['tot_con', 'tot_con_norm']) as cursor:
    for row in cursor:
        row[1] = (row[0] - minval) / (maxval - minval)
        cursor.updateRow(row)

# calculate 1-x of impacts so that higher values are more natural
with arcpy.da.UpdateCursor('sg_7_ranking', ['tot_imp_norm', 'naturalness']) as cursor:
    for row in cursor:
        row[1] = 1 - row[0]
        cursor.updateRow(row)

# add total impact and connectivity metrics for one overall metric
with arcpy.da.UpdateCursor('sg_7_ranking', ['tot_con_norm', 'naturalness', 'ranking_nonorm']) as cursor:
    for row in cursor:
        row[2] = row[0] + row[1]
        cursor.updateRow(row)

# normalize between 0 and 1
search_cursor = [row[0] for row in arcpy.da.SearchCursor('sg_7_ranking', ['ranking_nonorm'])]
maxval = max(search_cursor)
minval = min(search_cursor)
with arcpy.da.UpdateCursor('sg_7_ranking', ['ranking_nonorm', 'ranking_overall']) as cursor:
    for row in cursor:
        row[1] = (row[0] - minval) / (maxval - minval)
        cursor.updateRow(row)