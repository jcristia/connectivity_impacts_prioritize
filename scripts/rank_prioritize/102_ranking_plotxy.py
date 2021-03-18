# exploratory plots of just connectivity vs. impacts



import arcpy
import os
import pandas as pd
import seaborn as sns
#import matplotlib.pyplot as plt

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'main_seagrass.gdb'
sg = 'sg_7_ranking'
arcpy.env.workspace = os.path.join(root, gdb)

# arc table to pandas df
field_names = [i.name for i in arcpy.ListFields(sg) if i.type != 'OID']
cursor = arcpy.da.SearchCursor(sg, field_names)
df = pd.DataFrame(data=[row for row in cursor], columns=field_names)



# plot conn vs. impacts. There obviously won't be a relationship, but it will
# be good to show this.

# sns.set() # switch to seaborn aesthetics
# sns.set_style('white')
# sns.set_context('notebook')
splot = sns.regplot(data=df, x='tot_con_norm', y='naturalness')
fig = splot.get_figure()
fig.savefig('figs_out/conn_vs_impact.svg')
# so it looks like there actually is a little bit of a relationship, and this
# makes sense. Increasing connectivity results in decreasing naturalness. This
# is because of the regionally distributed impact metric.

# so let's try it without those included.
df_noconn = df.copy(deep=True)
df_noconn = df_noconn.drop(
    ['Shape', 'area_clipmpa', 'ORIG_FID', 'reg_sink', 'reg_sour', 'tot_imp', 'tot_con', 'tot_imp_norm', 'naturalness', 'ranking_nonorm', 'ranking_overall'],
    axis=1)
df_noconn['tot_imp'] = df_noconn.iloc[:, 2:8].sum(axis=1)
df_noconn['naturalness'] = 1 - (df_noconn.tot_imp - df_noconn.tot_imp.min())/(df_noconn.tot_imp.max()-df_noconn.tot_imp.min())
splot2 = sns.regplot(data=df_noconn, x='tot_con_norm', y='naturalness')
fig = splot2.get_figure()
fig.savefig('figs_out/conn_vs_impact_noregimpact.svg')
# The slope now flattens a bit.

