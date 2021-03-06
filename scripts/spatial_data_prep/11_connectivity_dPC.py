# assign Conefor dPC metrics to each seagrass meadow

# environments get switched part way through
# Hokey, but I'm still dealing with the arcpro-geopandas issue.

# attributes:
# dPC_pld01
# dPC_pld60
# dPC_ALL

# I am splittng by PLD so that we have a bit of a multispecies tradeoff, but I 
# want to keep it simple so that it is still easy enough to interpret.
# Based on chapter 1, I will consider short and long distance dispersers (1 vs. 60 days).
# Even though there will be local differences between 1-3-7-... days, the overall
# connectivity does not change much between 7-60 days. This is in terms of overall
# connectivity - so is the network connected enough for multigenerational movement.
# So even if there are individual step differences between these levels, a particle
# could still link up most of the network if they can disperse for more than 3
# days.

# Inititally I was going to just include the dPCinter component.
# But, after some investigation, there is very little difference between plds 
# for the inter components. They are very similar because the only kind of 
# connectivity that gets added after a day are just more rare connections. So 
# even though the number of connections increase, they are all weak connections, 
# so even there is an increase in values, they are hardly discernible.
# If we are going to to use PC metrics then we should use the full dPC metric. 
# I will include metrics for pld 1 and 60, but also the overall metric since 
# that might be all that we use.


import arcpy

import os
import pandas as pd
import numpy as np

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = os.path.join(root, 'connectivity_dPC.gdb')

chp1_root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Hakai\scripts_runs_cluster\seagrass'
dPC_ALL = r'output_figs_SALISHSEA_ALL\patch_centroids_metrics_ALL.shp'
chp1_folders = [
    'seagrass_20200228_SS201701',
    'seagrass_20200309_SS201705',
    'seagrass_20200309_SS201708',
    'seagrass_20200310_SS201101',
    'seagrass_20200310_SS201105',
    'seagrass_20200310_SS201108',
    'seagrass_20200327_SS201401',
    'seagrass_20200327_SS201405',
    'seagrass_20200327_SS201408'
]
conefor = 'conefor\conefor_connectivity_pld{}\conefor_metrics.shp'
plds = ['01', '60']

arcpy.env.workspace = os.path.join(root, gdb)

#####################################################

# Get overall dPC values

dPC_ALL_fc = os.path.join(chp1_root, dPC_ALL)
arcpy.CopyFeatures_management(dPC_ALL_fc, 'sg_dPC')
fields = arcpy.ListFields('sg_dPC')
keep = ['OBJECTID', 'Shape', 'uID', 'dPC', 'dPCintra', 'dPCflux', 'dPCconnect', 'dPCinter']
list_diff = [item.name for item in fields if item.name not in keep]
arcpy.DeleteField_management('sg_dPC', list_diff)
# uID is annoyingly a text field
arcpy.AddField_management('sg_dPC', 'uID_temp', 'SHORT')
with arcpy.da.UpdateCursor('sg_dPC', ['uID', 'uID_temp']) as cursor:
    for row in cursor:
        row[1] = int(row[0])
        cursor.updateRow(row)
arcpy.DeleteField_management('sg_dPC', 'uID')
arcpy.AddField_management('sg_dPC', 'uID', 'SHORT')
with arcpy.da.UpdateCursor('sg_dPC', ['uID_temp', 'uID']) as cursor:
    for row in cursor:
        row[1] = row[0]
        cursor.updateRow(row)
arcpy.DeleteField_management('sg_dPC', 'uID_temp')

#####################################################

# dPC scores by PLD

# switch enviroments. Hokey, but I can't get geopandas properly installed in my
# arcpro environment.

import geopandas as gp

for pld in plds:
    gdf = gp.GeoDataFrame()
    for dir in chp1_folders:
        path = os.path.join(chp1_root, dir, conefor.format(pld))
        df = gp.read_file(path)
        gdf = gdf.append(df)
    gdf_avg = gdf.groupby(['uID']).agg(
        dPC = ('dPC', 'mean'),
        dPCintra = ('dPCintra', 'mean'),
        dPCflux = ('dPCflux', 'mean'),
        dPCconnect = ('dPCconnect', 'mean')  
    ).reset_index()
    # rename fields
    gdf_avg = gdf_avg.rename(columns={
        'dPC':f'dPC_pld{pld}',
        'dPCintra':f'dPCintra_pld{pld}',
        'dPCflux':f'dPCflux_pld{pld}',
        'dPCconnect':f'dPCconnect_pld{pld}',
    })
    
    x = np.array(np.rec.fromrecords(gdf_avg.values))
    names = gdf_avg.dtypes.index.tolist()
    x.dtype.names = tuple(names)
    np.save(os.path.join(root, f'sg_dPC_pld{pld}'), x)


##########################################
# switch back to arcpy
# output array to esri table

files = os.listdir(root)
for file in files:
    file_name, file_ext = os.path.splitext(file)
    if file_ext == '.npy':
        arr = np.load(os.path.join(root, file))
        arcpy.da.NumPyArrayToTable(arr, os.path.join(arcpy.env.workspace, file_name))

files = os.listdir(root)
for file in files:
    file_name, file_ext = os.path.splitext(file)
    if file_ext == '.npy':
        os.remove(os.path.join(root, file))


##########################################
# join all together

tables = arcpy.ListTables()
arcpy.env.qualifiedFieldNames = False
for table in tables:
    arcpy.JoinField_management('sg_dPC', 'uID', table, 'uID')
    arcpy.DeleteField_management('sg_dPC', 'uID_1')

