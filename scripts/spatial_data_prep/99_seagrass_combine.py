# combine all impact and connectivity attributes into 1 seagrass dataset

import arcpy
import os


# Primary seagrass dataset
sg = r'main_seagrass.gdb\sg_2_canada'


# Impacts
population = 'population.gdb/sg_105_freq'
# Overwater structures:
# sg_07a_AREA gives me AREA PERCENT. It also still has the FREQUENCY field so
# that I can get a count.
# sg_07b_TYPECOUNT gives me the count of structure type in each buffer. This
# might be useful for noting the extra effects from aquaculture and wood waste
ow_area = 'overwater_structures.gdb/sg_07a_AREA'
ow_type = 'overwater_structures.gdb/sg_07b_TYPECOUNT'

shoreline_mod = 'shoreline_modification.gdb/sg_106_AREA'