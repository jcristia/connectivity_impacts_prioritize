# calculate regionally distributed impacts
# This is based on Jonsson et al 2020
# Essentially, this is source-sink dynamics and the transfer of impacts in the 
# form of lost recruits i.e. reduced dispersal from sites with high impacts and 
# reduced survival of recruits coming into high impacted sites.

# all other metrics have to be created before creating this one, and
# 97_seagrass_combine.py has to be ran
# Following running this script, you can then run script 99 to combine everything.

import arcpy
import os
import pandas as pd
import numpy as np


root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
outgdb = 'regional_connimpact.gdb'
conn_lines = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Hakai\scripts_runs_cluster\seagrass\output_figs_SALISHSEA_ALL\connectivity_average_ALL.shp' # these are the overall averaged connectivity lines
sg_og = os.path.join(root, 'main_seagrass.gdb/sg_2_canada')
impacts = os.path.join(root, 'main_seagrass.gdb/sg_4_join_norm')
arcpy.env.workspace = os.path.join(root, outgdb)


# read in connectivity lines as dataframe
field_names = [i.name for i in arcpy.ListFields(conn_lines) if i.type != 'OID']
cursor = arcpy.da.SearchCursor(conn_lines, field_names)
df_conn = pd.DataFrame(data=[row for row in cursor], columns=field_names)
df_conn = df_conn.drop(['Shape', 'freq', 'prob_stdf0', 'prob_std9', 'date', 'dateYR', 'dateSEA', 'timeintavg', 'timeintmin', 'timeintmax'], axis=1)
df_conn = df_conn[df_conn.from_id != df_conn.to_id]

# read in impacts as df
field_names = [i.name for i in arcpy.ListFields(impacts) if i.type != 'OID']
cursor = arcpy.da.SearchCursor(impacts, field_names)
df_imp = pd.DataFrame(data=[row for row in cursor], columns=field_names)
df_imp = df_imp.drop(
    ['Shape', 'area_clipmpa', 'percent_mpaoverlap', 'Shape_Length', 'Shape_Area',
    'dPCpld01', 'dPCpld60', 'sink_01', 'sink_60', 'source01', 'source60',
    'gpfill01', 'gpfill60']
    , axis=1)

# add up all impacts by meadow and normalize
df_imp['total'] = df_imp.iloc[:, 1:].sum(axis=1)
min = df_imp.total.min()
max = df_imp.total.max()
df_imp['total_norm'] = (df_imp.total - min) / (max - min)
df_imp = df_imp.drop(
    ['popn', 'ow_perc', 'aquacult', 'logboom', 'smodperc', 'agricult', 'cutblock', 'gcrab', 'total'],
    axis=1
)


# for each meadow, calculate source/sink distributed impact
uIDs = df_imp.uID.values
s_dict = {
    'uid':[],
    'sink':[],
    'source':[]
    }
for uid in uIDs:

    # get in/out connections
    in_conns = df_conn[df_conn.to_id == uid]
    ot_conns = df_conn[df_conn.from_id == uid]

    # get impacts for the uIDs coming in
    imps_in = df_imp[df_imp.uID.isin(in_conns.from_id)]
    # get impact for just the from meadow
    imp_ot = df_imp.total_norm[df_imp.uID == uid]

    # multiply impact by connectivity probability for incoming connections
    imps_mult_in = in_conns.merge(imps_in, left_on='from_id', right_on='uID')
    imps_mult_in['impconn'] = imps_mult_in.probavgm * imps_mult_in.total_norm
    # multiply home impact by conn prob for outgoing connections
    imps_mult_out = ot_conns
    imps_mult_out['impconn'] = ot_conns.probavgm * imp_ot.values[0]
    # sum
    sink = imps_mult_in.impconn.sum()
    source = imps_mult_out.impconn.sum()

    # add to dictionary
    s_dict['uid'].append(uid)
    s_dict['sink'].append(sink)
    s_dict['source'].append(source)


# turn dict to dataframe
df_all = pd.DataFrame.from_dict(s_dict)

# export to arc table
x = np.array(np.rec.fromrecords(df_all.values))
names = df_all.dtypes.index.tolist()
x.dtype.names = tuple(names)
arcpy.da.NumPyArrayToTable(x, os.path.join(arcpy.env.workspace, f'impconn_01_tbl'))