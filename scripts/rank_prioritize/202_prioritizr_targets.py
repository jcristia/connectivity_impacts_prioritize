# calculate targets for each feature

# First, I need to set an area target, which will guide the connectivity targets.
# See  'Design Strategies for the NSB MPA network' (draft version) for details.
# They used a 20-40% target for eelgrass in the NSB.
# I will get the total area and see what % is alreeady protected and subtract
# that from the initial target %. This will be my seagrass area target.
# I can also do a scenario with nothing locked out and the original 40% target.

# Then, I will set connectivity targets.
# I inititally tried the approach from Magris et al 2017, but it doesn't really
# make sense (see notes below).

# So for now I will just start with conn metrics at 16% as well. I will test 
# a range of targets for the conn features and calculate EC(PC) vs. cost.
# See the post analysis script.


import arcpy
import os
import pandas as pd

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'prioritizr.gdb'
arcpy.env.workspace = os.path.join(root, gdb)
sg = 'sg_01_copy'

# fc to df
field_names = [i.name for i in arcpy.ListFields(sg) if i.name not in ('OBJECTID', 'Shape')]
cursor = arcpy.da.SearchCursor(sg, field_names)
df = pd.DataFrame(data=[row for row in cursor], columns=field_names)

# AREA
area_target_initial = 0.30
total_seagrass_area = df.area.sum()
total_seagrass_protected = df.area_clipmpa.sum()
precent_seagrass_protected = total_seagrass_protected / total_seagrass_area
percent_to_protect = round(area_target_initial - precent_seagrass_protected, 2)
# this ends up being ~ 6%
# so when I lock out mpas, use 6%
# when I run a scenario without any restrictions, use 30%


# # ARCHIVING THIS FOR NOW:
# # CONNECTIVITY
# # This is based on the methodology from Magris et al 2017.
# # get the total amount for a column
# # get the total for the top third(?) of values. So for 653 meadows, this would be
# # the connectivity of the top ranked 217-8 meadows.
# # then divide that sum by the overall sum, and that is my target.
# # So in a way, let's say you want to conserve about 1/3 of seagrass area. Then
# # If you say that you want to conserve 1/3 of connectivity, since some meadows
# # dispproportionately contain a lot more connectivity than others, then you
# # might end up only selecting 5% of meadows to reach that 1/3 of connectivity.
# cols = ['dPCpld01', 'dPCpld60', 'sink_01', 'sink_60', 'source01', 'source60',
#        'gpfill01', 'gpfill60']

# # the output for this is simply a dictionary.
# # I'll just add them in to my R script manually.
# targets_area_all = {}
# targets_area_adj = {}

# # for initial % area targets:
# nrows = round(len(df) * area_target_initial)
# nrows = 14
# for col in cols:
#     # get sum
#     total = df[col].sum()
#     # get top % of rows
#     df_sort = df.sort_values(col, ascending=False).head(nrows)
#     total_toprows = df_sort[col].sum()
#     target_col = round(total_toprows / total, 2)
#     targets_area_all[col] = target_col

# # for reduced % area targets:
# nrows = round(len(df) * percent_to_protect)
# for col in cols:
#     # get sum
#     total = df[col].sum()
#     # get top % of rows
#     df_sort = df.sort_values(col, ascending=False).head(nrows)
#     total_toprows = df_sort[col].sum()
#     target_col = round(total_toprows / total, 2)
#     targets_area_adj[col] = target_col

# # I'll need to do some testing. The high numbers seem alarming, but...
# # for sink_01, the 110th meadow has a value of 0.009 (on a scale of 0-1).
# # BUT, if I have a target of 100% then it will just always select those meadows
# # and I won't see trade offs, hmmmmmmmm.
# # Now I wonder, does this even make sense? Why not just flat targets? Magris
# # doesn't cite anything for why they did it this way.
    
# # the dictionaries are my output. I can just enter these manually into my R script