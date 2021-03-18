# exploratory pca plots
# env: plotting

# see script 103 for notes on pca and different methods tried
# I'm using the plotly approach. It still uses sklearn like all the other
# methods, it just allows me to have interactive plots. This is super convenient
# when you have a lot of points. I can hover over certain points and find out
# their uID.
# https://plotly.com/python/pca-visualization/


# PCA in general:
# view multiple dimensions on 2 axes. Reduce the number of dimensions. View
# what is driving most of the variation and see which seagrass meadows load on
# which drivers.
#
# Geometrically speaking, principal components represent the directions of the 
# data that explain a maximal amount of variance, that is to say, the lines that
# capture most information of the data. The relationship between variance and 
# information here, is that, the larger the variance carried by a line, the 
# larger the dispersion of the data points along it, and the larger the 
# dispersion along a line, the more the information it has. To put all this 
# simply, just think of principal components as new axes that provide the best 
# angle to see and evaluate the data, so that the differences between the 
# observations are better visible.

# One thing to remember: this isn't necessarily telling me anything absolute
# about the values. It is simply showing what are the primary varibales that
# are making meadows VARY.


import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import plotly.express as px



# output arc table to csv
# do the stupid environment switching thing
# import arcpy
# intable = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\spatial\main_seagrass.gdb\sg_7_ranking'
# outlocation = r'C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\scripts\rank_prioritize'
# arcpy.TableToTable_conversion(intable, outlocation, 'sg_7_ranking.csv')


# read in csv as df
df = pd.read_csv('sg_7_ranking.csv')
df = df.drop(
    ['OBJECTID', 'area_clipmpa', 'ORIG_FID', 'tot_imp', 'tot_con', 
    'tot_imp_norm', 'tot_con_norm', 'naturalness', 'ranking_nonorm', 
    'ranking_overall'], 
    axis=1)


# do 3 series of plots: 
# just naturalness, just connectivity, and all together
# for each do:
# plot of each variable vs. every other
# plot of cumulative explained variance
# scatter and loadings plot




#####################
# 1 Naturalness
#####################

df_featall = df.copy(deep=True)
df_x = df_featall.iloc[:, 2:10]
#df_x = df_featall.iloc[:, 2:8] # use this one if you don't want to include the regionaly distributed impacts metrics
#df_x = 1.0 - df_x #(if you want to invert scores)
df_y = df_featall.loc[:, ['uID']]
x = StandardScaler().fit_transform(df_x)
x = pd.DataFrame(x, columns=df_x.columns)

# (1) every feature vs every other feature
fig = px.scatter_matrix(x)
fig.update_traces(diagonal_visible=False)
fig.show()
fig.write_html('figs_out/scatter_matrix_impacts.html')

# (2) cumulative explained variation
pca = PCA()
pca.fit(x)
exp_var_cumul = np.cumsum(pca.explained_variance_ratio_)
fig = px.area(
    x=range(1, exp_var_cumul.shape[0] + 1),
    y=exp_var_cumul,
    labels={"x": "# Components", "y": "Explained Variance"}
)
fig.show()
fig.write_html('figs_out/variation_explained_impacts.html')

# (3) scatter and loadings plot
pcamodel = PCA(n_components=2)
pca = pcamodel.fit_transform(x)
score = pca[:,0:2]
xs = score[:,0]
ys = score[:,1]
n = 2
scalex = 1.0/(xs.max() - xs.min())
scaley = 1.0/(ys.max() - ys.min())
fig = px.scatter(x=xs*scalex, y=ys*scaley, color=df_y['uID'] )
loadings = pcamodel.components_.T * np.sqrt(pcamodel.explained_variance_)
for i, feature in enumerate(x.columns):
    fig.add_shape(
        type='line',
        x0=0, y0=0,
        x1=loadings[i, 0],
        y1=loadings[i, 1]
    )
    fig.add_annotation(
        x=loadings[i, 0],
        y=loadings[i, 1],
        ax=0, ay=0,
        xanchor="center",
        yanchor="bottom",
        text=feature,
    )
fig.show()
fig.write_html('figs_out/pcaloadings_impacts.html')

# shoreline modification is driving a lot of the variation
# it is interesting to see it opposite of cutblocks. I guess that is because
# most cutblocks are in natural areas and they leave coastline buffers


#####################
# 2 Connectivity
#####################

df_featall = df.copy(deep=True)
df_x = df_featall.iloc[:, 10:]
df_y = df_featall.loc[:, ['uID']]
x = StandardScaler().fit_transform(df_x)
x = pd.DataFrame(x, columns=df_x.columns)

# (1) every feature vs every other feature
fig = px.scatter_matrix(x)
fig.update_traces(diagonal_visible=False)
fig.show()
fig.write_html('figs_out/scatter_matrix_conn.html')

# (2) cumulative explained variation
pca = PCA()
pca.fit(x)
exp_var_cumul = np.cumsum(pca.explained_variance_ratio_)
fig = px.area(
    x=range(1, exp_var_cumul.shape[0] + 1),
    y=exp_var_cumul,
    labels={"x": "# Components", "y": "Explained Variance"}
)
fig.show()
fig.write_html('figs_out/variation_explained_conn.html')

# (3) scatter and loadings plot
pcamodel = PCA(n_components=2)
pca = pcamodel.fit_transform(x)
score = pca[:,0:2]
xs = score[:,0]
ys = score[:,1]
n = 2
scalex = 1.0/(xs.max() - xs.min())
scaley = 1.0/(ys.max() - ys.min())
fig = px.scatter(x=xs*scalex, y=ys*scaley, color=df_y['uID'] )
loadings = pcamodel.components_.T * np.sqrt(pcamodel.explained_variance_)
for i, feature in enumerate(x.columns):
    fig.add_shape(
        type='line',
        x0=0, y0=0,
        x1=loadings[i, 0],
        y1=loadings[i, 1]
    )
    fig.add_annotation(
        x=loadings[i, 0],
        y=loadings[i, 1],
        ax=0, ay=0,
        xanchor="center",
        yanchor="bottom",
        text=feature,
    )
fig.show()
fig.write_html('figs_out/pcaloadings_conn.html')

# so from this I see... dPC is driving a lot of the variation,
# meadows are different in their ability to act as a source/sink to mpas vs.
# acting as a gap filler


#####################
# 3 ALL
#####################

df_featall = df.copy(deep=True)
df_x = df_featall.iloc[:, 2:]
df_y = df_featall.loc[:, ['uID']]
x = StandardScaler().fit_transform(df_x)
x = pd.DataFrame(x, columns=df_x.columns)

# (1) every feature vs every other feature
fig = px.scatter_matrix(x)
fig.update_traces(diagonal_visible=False)
fig.show()
fig.write_html('figs_out/scatter_matrix_all.html')

# (2) cumulative explained variation
pca = PCA()
pca.fit(x)
exp_var_cumul = np.cumsum(pca.explained_variance_ratio_)
fig = px.area(
    x=range(1, exp_var_cumul.shape[0] + 1),
    y=exp_var_cumul,
    labels={"x": "# Components", "y": "Explained Variance"}
)
fig.show()
fig.write_html('figs_out/variation_explained_all.html')

# (3) scatter and loadings plot
pcamodel = PCA(n_components=2)
pca = pcamodel.fit_transform(x)
score = pca[:,0:2]
xs = score[:,0]
ys = score[:,1]
n = 2
scalex = 1.0/(xs.max() - xs.min())
scaley = 1.0/(ys.max() - ys.min())
fig = px.scatter(x=xs*scalex, y=ys*scaley, color=df_y['uID'] )
loadings = pcamodel.components_.T * np.sqrt(pcamodel.explained_variance_)
for i, feature in enumerate(x.columns):
    fig.add_shape(
        type='line',
        x0=0, y0=0,
        x1=loadings[i, 0],
        y1=loadings[i, 1]
    )
    fig.add_annotation(
        x=loadings[i, 0],
        y=loadings[i, 1],
        ax=0, ay=0,
        xanchor="center",
        yanchor="bottom",
        text=feature,
    )
fig.show()
fig.write_html('figs_out/pcaloadings_all.html')

# One thing to remember: this isn't necessarily telling me anything absolute
# about the values. It is simply showing what are the primary varibales that
# are making meadows VARY.
# the connectivity is causing meadows to vary a lot more than impacts
# BUT remember, these 2 axes are only explaining 42 percent of the variation,
# so in a way, many of things are needed to explain the differences in meadows.

# so I guess in  away, this is why we need a tool like prioritizr? Otherwise,
# our basic ranking will just end up choosing meadows based on high connectivity
# values. Whereas with prioritizR, we can set a target for each conn metric and
# then use the impacts separately as penalties.