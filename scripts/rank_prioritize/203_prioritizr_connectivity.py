# format connectivity line dataframe for input into prioritizr as a connectivity
# penalty

# The required format requires some wrangling of my connectivity lines.
# Fields: 'id1', 'id2', 'boundary'
# A connection is assumed to be symmetric unless there is a record for the 
# opposite direction.


import arcpy
import os
import pandas as pd

conn_lines = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Hakai\scripts_runs_cluster\seagrass\output_figs_SALISHSEA_ALL\connectivity_average_ALL.shp'
sg_canada = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial\prioritizr.gdb\sg_02_pt'
out_dir = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\scripts\prioritizr_seagrass'


# get list of uIDs for Canadian seagrass
uids = [row[0] for row in arcpy.da.SearchCursor(sg_canada, 'id')]

# read conn lines into pandas dataframe
field_names = [i.name for i in arcpy.ListFields(conn_lines) if i.type != 'OID']
cursor = arcpy.da.SearchCursor(conn_lines, field_names)
df = pd.DataFrame(data=[row for row in cursor], columns=field_names)
df = df[['from_id', 'to_id', 'probavgm']]

# change field names to match what is required by prioritizr
df = df.rename(columns={'from_id':'id1', 'to_id':'id2', 'probavgm':'boundary'})

# change float to int
df.id1 = df.id1.astype('int')
df.id2 = df.id2.astype('int')

# remove self connections
df = df[df.id1 != df.id2]

# remove connections less than 0.000001 (prioritizr gives a warning/error for
# numerical stability reasons)
df = df[df.boundary > 0.000001]

# remove connections outside of Canada
df = df[df.id1.isin(uids) & df.id2.isin(uids)]

# Go through each connection, check if the opposite connection exists.
# If it does not then add a new row to a separate dictionary with that opposite 
# connection and a value of 0. Concatenate.
dict = {
    'id1':[],
    'id2':[],
    'boundary':[]
}
for row in df.itertuples(index=False):
    x = df[(df.id1==row[1]) & (df.id2==row[0])].empty
    if x: # if empty
        dict['id1'].append(row[1])
        dict['id2'].append(row[0])
        dict['boundary'].append(0)
df_dict = pd.DataFrame(dict)
df = pd.concat([df, df_dict])

## SO PRIORITIZR DOES actually recognize the uID value
# # Prioritizr doesn't actually use the uID I give it (it does retian it as a 
# # column though). So I need to add a sequential id.
# # Read uID list as df, order by uID, then add another id column and fill 
# # sequentially. Then for each from and to, change uID to this new id.
# df_uid = pd.DataFrame(uids, columns=['uid'])
# df_uid['new_id'] = df_uid.index + 1 # r is 1 index
# lkup = dict(zip(df_uid.uid, df_uid.new_id))
# df.id1 = df.id1.replace(lkup)
# df.id2 = df.id2.replace(lkup)

# Output to csv
df.to_csv(os.path.join(out_dir, 'connectivity.csv'), index=False)