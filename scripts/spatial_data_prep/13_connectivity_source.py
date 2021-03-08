# calculate the amount of recruits that move from seagrass meadows to MPAs

# This can tell us:
#   (1) if it is a source to MPAs then it can be a link in the existing network
#       of mpas

# Attributes:
# 	source_to_mpa_count_pld01
# 	source_to_mpa_count_pld60

# For the sink metric, I will include particles that came from US MPAs. However,
# for the source metric, I will only consider connections to Canadian coastline.

# OVERALL WITH ALL THESE METRICS:
# This is not a perfect solution. This is the best I can do. It will simply
# need to be viewed as an estimation with some error involved.

import arcpy
import os
import pandas as pd

root = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial'
gdb = 'connectivity_source.gdb'
arcpy.env.workspace = os.path.join(root, gdb)

# seagrass chapter 1 results
sg_dir = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Hakai\scripts_runs_cluster\seagrass'
dest_pts = os.path.join(sg_dir, 'seagrass_{}\seagrass_{}\outputs\shp\dest_biology_pts_sg{}.shp')
dates = [
    '20200228_SS201701',
    '20200309_SS201705',
    '20200309_SS201708',
    '20200310_SS201101',
    '20200310_SS201105',
    '20200310_SS201108',
    '20200327_SS201401',
    '20200327_SS201405',
    '20200327_SS201408'
]
sections = list(range(1,10))

# coastline used for seagrass connectivity
coastline = os.path.join(root, 'main_seagrass.gdb/coastline_bc_ak_wa_or_cleaned_less10000')
# coastline used for mpa connectivity
coastline_mpa = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\spatial\Coastline\coastline.gdb\landmask_FINAL'

plds = [1, 60]

# Canada portion of Salish Sea
salishsea_canada = r'salishsea_canada_clippoly'

# Seagrass in Canada
sg_canada = os.path.join(root, 'main_seagrass.gdb/sg_2_canada')

# MPAs
mpas = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\MPA_connectivity\spatial\MPA\mpas.gdb\M08_mpa_20201124_FINALCOPY'


###################################################
# Source-to-MPA metric

def selectAndCombineDestPts(dest_pts, dates, sections, pld, sg_canada, salishsea_canada):
    """
    Combine destination points from the seagrass study.
    Select particles:
        -originating in Canadian seagrass
        -no self-retention        
        -by mortality
        -where particle strands or settles before PLD
    Clip to Canada
    Merge
    """

    # get list of uIDs for seagrass in Canada
    uIDs_can = tuple(list([i[0] for i in arcpy.da.SearchCursor(sg_canada, 'uID')]))

    # calculate pld_int
    pld_int = pld * 48 - 1 # 0 index

    i=0
    for date in dates:
        for section in sections:
            shp = dest_pts.format(date, section, section)
            arcpy.MakeFeatureLayer_management(shp, 'temp_lyr')
            arcpy.SelectLayerByAttribute_management(
                'temp_lyr',
                'NEW_SELECTION',
                f'"uID" IN {uIDs_can}'
            )
            arcpy.SelectLayerByAttribute_management(
                'temp_lyr',
                'SUBSET_SELECTION',
                '"uID" <> "dest_id"'
            )
            arcpy.SelectLayerByAttribute_management(
                'temp_lyr',
                'SUBSET_SELECTION',
                f'mortstep = -1 Or mortstep >= ({pld_int} + time_int_s)'
            )            
            arcpy.SelectLayerByAttribute_management(
                'temp_lyr',
                'SUBSET_SELECTION',
                f'(time_int - time_int_s) <= {pld_int}'
            )      
            arcpy.Clip_analysis('temp_lyr', salishsea_canada, f'tmp_dest_pts_{i}')
            i+=1
            arcpy.Delete_management('temp_lyr')            

    fcs = arcpy.ListFeatureClasses('tmp_dest_pts_*')
    arcpy.Merge_management(fcs, f'destpts_01_pld{str(pld)}_selectMerge')
    for fc in fcs:
        arcpy.Delete_management(fc)


def coastlineUID(coastline, coastline_mpa):
    """
    Establish association between different coastlines.

    There are areas where doing a near analysis to the MPA coast would
    result in a particle being moved to the wrong coastline.
    """
    
    arcpy.CopyFeatures_management(coastline, 'coastline_01a_sg')
    arcpy.CopyFeatures_management(coastline_mpa, 'coastline_01b_mpa')
    arcpy.AddField_management('coastline_01a_sg', 'coast_uID_sg', 'SHORT')
    arcpy.AddField_management('coastline_01b_mpa', 'coast_uID_mpa', 'SHORT')
    with arcpy.da.UpdateCursor('coastline_01a_sg', ['OBJECTID', 'coast_uID_sg']) as cursor:
        for row in cursor:
            row[1]=row[0]
            cursor.updateRow(row)
    with arcpy.da.UpdateCursor('coastline_01b_mpa', ['OBJECTID', 'coast_uID_mpa']) as cursor:
        for row in cursor:
            row[1]=row[0]
            cursor.updateRow(row)

    arcpy.SpatialJoin_analysis(
        'coastline_01a_sg',
        'coastline_01b_mpa',
        'coastline_02_spatialjoin',
        'JOIN_ONE_TO_MANY',
        'KEEP_ALL',
        match_option='INTERSECT'
    )



def adjustPointsToMpaOrSgCoast(pld, coastline, mpas):
    """
    Move points to the nearest mpa or coast (seagrass version).

    There are some areas that have an mpa and seagrass coast, but no mpa coast.
    Therefore, turn seagrass coast and mpas into lines together.
    Do Near analysis with these.
    Make pts.

    There will be a little error associated with this, but it should be minimal.
    """
    if not arcpy.Exists('coastline_03_mpamerge'):
        arcpy.Merge_management([coastline, mpas], 'coastline_03_mpamerge')
        arcpy.PolygonToLine_management('coastline_03_mpamerge', 'coastline_04_line')
    
    fc = f'destpts_01_pld{str(pld)}_selectMerge'
    arcpy.CopyFeatures_management(fc, f'destpts_02_pld{str(pld)}_near')
    arcpy.Near_analysis(f'destpts_02_pld{str(pld)}_near', 'coastline_04_line', location='LOCATION')
    arcpy.TableToTable_conversion(f'destpts_02_pld{str(pld)}_near', arcpy.env.workspace, f'destpts_03_pld{str(pld)}_neartbl')
    arcpy.MakeXYEventLayer_management(
        f'destpts_03_pld{str(pld)}_neartbl', 
        'NEAR_X', 
        'NEAR_Y', 
        'tmplyr',
        3005)
    arcpy.CopyFeatures_management('tmplyr', f'destpts_04_pld{str(pld)}_nearpts')
    arcpy.Delete_management('tmplyr')


def removeSelectPts(pld, mpas):
    """
    Remove points that are already intersecting an mpa. I don't want to adjust 
    them if they already intersect.
    Then remove points that intersect a portion of the seagrass coastline version
    but where there is not mpa coastline (usually small islands).
    """

    # remove points that are already intersecting an mpa (save these to add back in later)
    if not arcpy.Exists(f'destpts_05_pld{str(pld)}_mpainter'):
        arcpy.Clip_analysis(
            f'destpts_04_pld{str(pld)}_nearpts', 
            mpas, 
            f'destpts_05_pld{str(pld)}_mpainter')
        arcpy.MakeFeatureLayer_management(f'destpts_04_pld{str(pld)}_nearpts', 'tmp_lyr')
        arcpy.SelectLayerByLocation_management(
            'tmp_lyr',
            'INTERSECT',
            mpas,
            invert_spatial_relationship='INVERT'
        )
        arcpy.CopyFeatures_management('tmp_lyr', f'destpts_06_pld{str(pld)}_nompainter')
        arcpy.Delete_management('tmp_lyr')

    # remove pts that are on sg coast where there is no intersecting mpa coast
    if not arcpy.Exists(f'destpts_07_pld{str(pld)}_remove'):
        arcpy.SpatialJoin_analysis(
            f'destpts_06_pld{str(pld)}_nompainter',
            'coastline_01a_sg',
            f'destpts_07_pld{str(pld)}_remove',
            'JOIN_ONE_TO_ONE',
            'KEEP_ALL',
            match_option='INTERSECT'
        )
    arcpy.CopyFeatures_management(f'destpts_07_pld{str(pld)}_remove', f'destpts_08_pld{str(pld)}_remove')
    # get coast_uID_sg where coast_uID_mpa is None
    sg_coast_no_mpacoast = []
    with arcpy.da.SearchCursor('coastline_02_spatialjoin', ['coast_uID_sg', 'coast_uID_mpa']) as cursor:
        for row in cursor:
            if row[1] == None:
                if row[0] not in sg_coast_no_mpacoast:
                    sg_coast_no_mpacoast.append(row[0])
    # remove
    with arcpy.da.UpdateCursor(f'destpts_08_pld{str(pld)}_remove', ['coast_uID_sg']) as cursor:
        for row in cursor:
            if row[0] in sg_coast_no_mpacoast:
                cursor.deleteRow()


def adjustPointsToCoast(pld, mpas, coastline_mpa):
    """
    Move points to the nearest coast (mpa version), so I can then assign these
    to an mpa. This is accounting for particles that were adjusted earlier to be
    on the sg coast but where they should still overlap with an mpa.

    """
    if not arcpy.Exists('coastline_05_line'):
        arcpy.PolygonToLine_management(coastline_mpa, 'coastline_05_line')
    
    fc = f'destpts_08_pld{str(pld)}_remove'
    arcpy.CopyFeatures_management(fc, f'destpts_09_pld{str(pld)}_near')
    fields = ['NEAR_FID', 'NEAR_DIST', 'NEAR_X', 'NEAR_Y']
    for field in fields:
        arcpy.DeleteField_management(f'destpts_09_pld{str(pld)}_near', field)
    arcpy.Near_analysis(
        f'destpts_09_pld{str(pld)}_near', 
        'coastline_05_line', 
        location='LOCATION',
        )
    arcpy.TableToTable_conversion(f'destpts_09_pld{str(pld)}_near', arcpy.env.workspace, f'destpts_10_pld{str(pld)}_neartbl')
    arcpy.MakeXYEventLayer_management(
        f'destpts_10_pld{str(pld)}_neartbl', 
        'NEAR_X', 
        'NEAR_Y', 
        'tmplyr',
        3005)
    arcpy.CopyFeatures_management('tmplyr', f'destpts_11_pld{str(pld)}_nearpts')
    arcpy.Delete_management('tmplyr')    


def removeParticlesNoMatch(pld):
    """
    Remove particles that snapped to a different coastline.
    """
    if not arcpy.Exists(f'destpts_12_pld{str(pld)}_remove'):
        arcpy.SpatialJoin_analysis(
            f'destpts_11_pld{str(pld)}_nearpts',
            'coastline_01b_mpa',
            f'destpts_12_pld{str(pld)}_remove',
            'JOIN_ONE_TO_ONE',
            'KEEP_ALL',
            match_option='INTERSECT'
        )
        arcpy.CopyFeatures_management(f'destpts_12_pld{str(pld)}_remove', f'destpts_13_pld{str(pld)}_remove')

    # get ID combinations as df
    field_names = ['coast_uID_sg', 'coast_uID_mpa']    
    cursor = arcpy.da.SearchCursor('coastline_02_spatialjoin', field_names)
    df_coast = pd.DataFrame(data=[row for row in cursor], columns=field_names)
    # get pts as dataframe
    field_names = ['coast_uID_sg', 'coast_uID_mpa', 'traj_id']    
    cursor = arcpy.da.SearchCursor(f'destpts_13_pld{str(pld)}_remove', field_names)
    df_pts = pd.DataFrame(data=[row for row in cursor], columns=field_names)
    # merge - this adds a field to show which part the field comes from, then
    # gets only where the right side is null (so no match to ID combination)
    df_merge = df_pts.merge(
        df_coast, 
        'outer', 
        left_on=['coast_uID_sg', 'coast_uID_mpa'], 
        right_on=['coast_uID_sg', 'coast_uID_mpa'],
        indicator='i'
        ).query('i=="left_only"').drop('i', 1)
    trajs = df_merge['traj_id'].tolist()
    # remove
    with arcpy.da.UpdateCursor(f'destpts_13_pld{str(pld)}_remove', ['traj_id']) as cursor:
        for row in cursor:
            if row[0] in trajs:
                cursor.deleteRow()

       
def pointsInMpas(pld, mpas):
    """
    Select the adjusted points that intersect MPAs
    """

    # buffer mpas by 30m to account for any boundary mismatch
    if not arcpy.Exists('mpas_01_buff30'):
        arcpy.Buffer_analysis(mpas, 'mpas_01_buff30', 30)
    arcpy.MakeFeatureLayer_management(f'destpts_13_pld{str(pld)}_remove', 'tmp_lyr')
    arcpy.SelectLayerByLocation_management(
        'tmp_lyr',
        'INTERSECT',
        'mpas_01_buff30',
    )
    arcpy.CopyFeatures_management('tmp_lyr', f'destpts_14_pld{str(pld)}_clip')
    arcpy.Delete_management('tmp_lyr')

    # merge with previous mpa points
    arcpy.Merge_management(
        [f'destpts_14_pld{str(pld)}_clip', f'destpts_05_pld{str(pld)}_mpainter'],
        f'destpts_15_pld{str(pld)}_mpamerge'
        )


def calcSource(pld):
    """
    Calculate the source potential of each seagrass meadow to each MPA.

    Add up points by uID.
    I'm not interested in the sink potential of a specific MPA, only the source
    potential of seagrass meadows to those mpas.

    Create table.
    """
    fc = f'destpts_15_pld{str(pld)}_mpamerge'
    arcpy.AddField_management(fc, 'pcount', 'SHORT')
    with arcpy.da.UpdateCursor(fc, 'pcount') as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)
    arcpy.Frequency_analysis(fc, f'sg_01_pld{str(pld)}_freq', 'uID', 'pcount')
    


#coastlineUID(coastline, coastline_mpa)
for pld in plds:
    #selectAndCombineDestPts(dest_pts, dates, sections, pld, sg_canada, salishsea_canada)
    #adjustPointsToMpaOrSgCoast(pld, coastline, mpas)
    #removeSelectPts(pld, mpas)
    #adjustPointsToCoast(pld, mpas, coastline_mpa)
    #removeParticlesNoMatch(pld)
    #pointsInMpas(pld, mpas)
    #calcSource(pld)