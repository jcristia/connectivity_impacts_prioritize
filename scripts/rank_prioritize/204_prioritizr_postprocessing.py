# read prioritizr outputs into fgdb, calculate selection frequency

import arcpy
import os
import pandas as pd
import numpy as np


root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts'
output_dir = 'scripts/prioritizr_seagrass/outputs'
gdb = 'spatial/prioritizr.gdb'
arcpy.env.workspace = os.path.join(root, gdb)
arcpy.env.qualifiedFieldNames = False


dirs = os.listdir(os.path.join(root, output_dir))

# create a feature class for each solution
for dir in dirs:
    solution = os.path.join(root, output_dir, dir, 'solution.csv')
    df = pd.read_csv(solution)

    # calculate selection frequency
    cols = ['id', 'rc']
    sol_cols = [col for col in df.columns if col.startswith('solution')]
    cols.extend(sol_cols)
    df = df[cols]
    df['sel_freq'] = df.loc[:, sol_cols].sum(axis=1) / len(sol_cols)

    # keep just the top solution
    df = df[['id', 'rc', 'solution_1', 'sel_freq']]

    # output to gdb table
    x = np.array(np.rec.fromrecords(df.values))
    names = df.dtypes.index.tolist()
    x.dtype.names = tuple(names)
    arcpy.da.NumPyArrayToTable(x, os.path.join(arcpy.env.workspace, 'sg_tbl_TEMP'))
    # join to copy of point feature class
    jointbl = arcpy.AddJoin_management('sg_02_pt', 'id', 'sg_tbl_TEMP', 'id')
    #sol_num = dir.split('_')[0]
    sol_num = dir
    arcpy.CopyFeatures_management(jointbl, f'sg_{sol_num}')
    arcpy.DeleteField_management(f'sg_{sol_num}', ['OBJECTID_1', 'id_1'])
    arcpy.Delete_management(jointbl)
    arcpy.Delete_management('sg_tbl_TEMP')



# it will also be helpful to have sel_freq, importance, and solution_1 split
# out into different fcs and have a column for each scenario
i = 0
for dir in dirs:
    solution = os.path.join(root, output_dir, dir, 'solution.csv')
    df = pd.read_csv(solution)
    sol_num = dir.split('_')[0]

    # calculate selection frequency
    cols = ['id', 'rc']
    sol_cols = [col for col in df.columns if col.startswith('solution')]
    cols.extend(sol_cols)
    df = df[cols]
    df['sel_freq'] = df.loc[:, sol_cols].sum(axis=1) / len(sol_cols)

    # keep just the top solution
    df = df[['id', 'rc', 'solution_1', 'sel_freq']]
    # make unique column names
    df = df.rename(columns={
        'rc':f'{sol_num}_rc',
        'solution_1':f'{sol_num}_sol1',
        'sel_freq':f'{sol_num}_selfreq'
    })

    # put into individual dataframes
    df_rc = df[['id', f'{sol_num}_rc']]
    df_sol1 = df[['id', f'{sol_num}_sol1']]
    df_selfreq = df[['id', f'{sol_num}_selfreq']]

    # append to individual dataframes
    if i == 0:
        df_rc_all = df_rc
        df_sol1_all = df_sol1
        df_selfreq_all = df_selfreq
    else:
        df_rc_all = df_rc_all.merge(df_rc, on='id')
        df_sol1_all = df_sol1_all.merge(df_sol1, on='id')
        df_selfreq_all = df_selfreq_all.merge(df_selfreq, on='id')
    i += 1

dfs = [df_rc_all, df_sol1_all, df_selfreq_all]
names = ['sg_all_rc', 'sg_all_solution1', 'sg_all_selfreq']
for df, name in zip(dfs, names):
    # output to gdb table
    x = np.array(np.rec.fromrecords(df.values))
    names = df.dtypes.index.tolist()
    x.dtype.names = tuple(names)
    arcpy.da.NumPyArrayToTable(x, os.path.join(arcpy.env.workspace, 'sg_tbl_TEMP'))
    # join to copy of point feature class
    jointbl = arcpy.AddJoin_management('sg_02_pt', 'id', 'sg_tbl_TEMP', 'id')
    arcpy.CopyFeatures_management(jointbl, name)
    arcpy.DeleteField_management(name, ['OBJECTID_1', 'id_1'])
    arcpy.Delete_management(jointbl)
    arcpy.Delete_management('sg_tbl_TEMP')



# stop there for now. Analysing the other summary tables can wait until I talk
# to Emily and figure out what I want to get out of this.
