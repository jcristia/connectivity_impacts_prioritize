# Find the percentage of a meadow that is covered by an mpa

# I want impact and connectivity values for all meadows, but there are some
# meadows that are already protected, so I should have a way to filter these
# out.


import arcpy
import os

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'main_seagrass.gdb'
sg = 'sg_2_canada'
mpas = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\spatial\MPA\mpas.gdb\M08_mpa_20201124_FINALCOPY'

arcpy.env.workspace = os.path.join(root, gdb)

arcpy.CopyFeatures_management(sg, 'sg_2_canada_copy')
arcpy.AddField_management('sg_2_canada_copy', 'area_clipmpa', 'FLOAT')
arcpy.AddField_management('sg_2_canada_copy', 'area_total', 'FLOAT')
with arcpy.da.UpdateCursor('sg_2_canada_copy', ['Shape_Area', 'area_total']) as cursor:
    for row in cursor:
        row[1] = row[0]
        cursor.updateRow(row)

arcpy.Clip_analysis('sg_2_canada_copy', mpas, 'sg_3_overlapmpa')

with arcpy.da.UpdateCursor('sg_3_overlapmpa', ['Shape_Area', 'area_clipmpa']) as cursor:
    for row in cursor:
        row[1] = row[0]
        cursor.updateRow(row)

arcpy.Delete_management('sg_2_canada_copy')
arcpy.AddField_management('sg_3_overlapmpa', 'percent_mpaoverlap', 'FLOAT')
with arcpy.da.UpdateCursor('sg_3_overlapmpa', ['area_total', 'area_clipmpa', 'percent_mpaoverlap']) as cursor:
    for row in cursor:
        row[2] = row[1]/row[0] * 100
        cursor.updateRow(row)

arcpy.env.qualifiedFieldNames = False
joined_table = arcpy.AddJoin_management(
    'sg_2_canada', 'uID', 'sg_3_overlapmpa', 'uID'
)
arcpy.CopyFeatures_management(joined_table, 'sg_3_percentmpaOverlap')

field_names = [f.name for f in arcpy.ListFields('sg_3_percentmpaOverlap')]
keep = ['Shape_Length', 'Shape', 'uID', 'area_clipmpa', 'percent_mpaoverlap', 'OBJECTID', 'Shape_Area']
for field in field_names:
    if field not in keep:
        try:
            # this doesn't always work. Schema lock issues.
            # just do it manually if it fails
            arcpy.DeleteField_management('sg_3_percentmpaOverlap', field)
        except:
            print('Delete field did not succeed')

arcpy.Delete_management('sg_3_overlapmpa')

