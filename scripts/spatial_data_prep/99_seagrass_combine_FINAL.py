# combine all impact and connectivity attributes into 1 seagrass dataset

# The last 3 scripts were thought out at different times, so this ends up being
# a bit repetitive, but it all runs quick, so I'm not going to take time to
# reconfigure it.


import arcpy
import os
import pandas as pd
import numpy as np


# Primary seagrass dataset
root = 'C:/Users/jcristia/Documents/GIS/MSc_Projects/Impacts/spatial'
arcpy.env.workspace = os.path.join(root, 'main_seagrass.gdb')

sg = 'sg_3_percentmpaOverlap'


#####################################################
# Impacts
population = 'population.gdb/sg_105_freq'
ow_area = 'overwater_structures.gdb/sg_07a_AREA'
shoreline_mod = 'shoreline_modification.gdb/sg_106_AREA'
agriculture = 'agriculture_watershed.gdb/sg_105_freq'
cutblocks = 'cutblocks_watershed.gdb/sg_105_freq'
greencrab = 'greencrab.gdb/sg_03_freq'

impacts_distributed = 'regional_connimpact.gdb/impconn_01_tbl'

# Connectivity
dPC_01 = 'connectivity_dPC.gdb/sg_dPC_pld01'
dPC_60 = 'connectivity_dPC.gdb/sg_dPC_pld60'
sink_01 = 'connectivity_sink.gdb/sg_pld1_03_freq'
sink_60 = 'connectivity_sink.gdb/sg_pld60_03_freq'
source_01 = 'connectivity_source.gdb/sg_01_pld1_freq'
source_60 = 'connectivity_source.gdb/sg_01_pld60_freq'
gapfill_01 = 'connectivity_gapfill_results.gdb/sg_01_pld1_gaptotal'
gapfill_60 = 'connectivity_gapfill_results.gdb/sg_01_pld60_gaptotal'


#########################################################

# dictionary of datasets and relevant fields
ds_dict = {
    population: ['SUM_pop_adjusted'],
    ow_area: ['ow_percent'],
    shoreline_mod: ['shmod_percent'],
    agriculture: ['percent_cropland'],
    cutblocks: ['percent_cutblocks'],
    greencrab: ['gc_presence'],
    impacts_distributed: ['sink', 'source'],
    dPC_01: ['dPC_pld01'],
    dPC_60: ['dPC_pld60'],
    sink_01: ['sink_particles'],
    sink_60: ['sink_particles'],
    source_01: ['pcount'],
    source_60: ['pcount'],
    gapfill_01: ['gapTotal'],
    gapfill_60: ['gapTotal']
}

# new names for fields since I stupidly didn't give them proper names initially
new_fields = [
    'popn',
    'ow_perc',
    'smodperc',
    'agricult',
    'cutblock',
    'gcrab',
    'reg_sink',
    'reg_sour',
    'dPCpld01',
    'dPCpld60',
    'sink_01',
    'sink_60',
    'source01',
    'source60',
    'gpfill01',
    'gpfill60'
]

#########################################################
# put all into pandas df

uIDs = list(set([i[0] for i in arcpy.da.SearchCursor(sg, 'uID')]))
df = pd.DataFrame(uIDs, columns=['uID'])

i=0
for ds in ds_dict:
    fc = os.path.join(root, ds)
    for field in ds_dict[ds]:
        newname = new_fields[i]
        i += 1
        # get uID field name in case it was changed
        uID = [f.name for f in arcpy.ListFields(fc) if f.aliasName == 'uID'][0]
        cursor = arcpy.da.SearchCursor(fc, [uID, field])
        df_temp = pd.DataFrame(data=[row for row in cursor], columns=['uID', newname])
        df = df.merge(df_temp, 'left', 'uID')


############################################################
# absolute values

df = df.fillna(0) 
x = np.array(np.rec.fromrecords(df.values))
names = df.dtypes.index.tolist()
x.dtype.names = tuple(names)
arcpy.da.NumPyArrayToTable(x, os.path.join(arcpy.env.workspace, f'sg_98_tbl'))
    
arcpy.env.qualifiedFieldNames = False
jt = arcpy.AddJoin_management(sg, 'uID', 'sg_98_tbl', 'uID')
arcpy.CopyFeatures_management(jt, 'sg_5_join')
arcpy.Delete_management('sg_98_tbl')
arcpy.DeleteField_management('sg_5_join', ['OBJECTID_1', 'UID_1'])
with arcpy.da.UpdateCursor('sg_5_join', ['area_clipmpa', 'percent_mpaoverlap']) as cursor:
    for row in cursor:
        if row[0] == None:
            row[0] = 0
        if row[1] == None:
            row[1] = 0
        cursor.updateRow(row)

##############################################################
# normalize values

df_n = df.copy(deep=True)

for co in df_n.columns:
    if co != 'uID':
        min = df_n[co].min()
        max = df_n[co].max()
        df_n[f'n{co}'] = (df_n[co]-min)/(max-min)
        df_n = df_n.drop([co], axis=1)
for co in df_n.columns:
    if co !='uID':
        df_n = df_n.rename(columns={co:co[1:]})

x = np.array(np.rec.fromrecords(df_n.values))
names = df_n.dtypes.index.tolist()
x.dtype.names = tuple(names)
arcpy.da.NumPyArrayToTable(x, os.path.join(arcpy.env.workspace, f'sg_99_tbl'))
    
arcpy.env.qualifiedFieldNames = False
jt = arcpy.AddJoin_management(sg, 'uID', 'sg_99_tbl', 'uID')
arcpy.CopyFeatures_management(jt, 'sg_5_join_norm')
arcpy.Delete_management('sg_99_tbl')
arcpy.DeleteField_management('sg_5_join_norm', ['OBJECTID_1', 'UID_1'])
with arcpy.da.UpdateCursor('sg_5_join_norm', ['area_clipmpa', 'percent_mpaoverlap']) as cursor:
    for row in cursor:
        if row[0] == None:
            row[0] = 0
        if row[1] == None:
            row[1] = 0
        cursor.updateRow(row)


# make these also output to pts too
arcpy.FeatureToPoint_management('sg_5_join_norm', 'sg_6_norm', 'INSIDE')