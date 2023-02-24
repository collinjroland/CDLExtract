# -*- coding: utf-8 -*-
"""
Created on Mon Feb 20 08:11:59 2023

@author: cjr2

GeneralCLDExtract.py
Extracts land cover types for a given shapefile from a supplied Cropland Data ...
Layer Raster and writes to CSV, can also export clipped TIFs and plot the resulting ...
CDL data with grouping together of classifications for easier interpretation
Author: Collin Roland
Last modified: 2023/02/23
TO DO:
"""
# %% Import packages
import geopandas as gpd
import rasterio
from rasterio.plot import show
import rasterio.mask
import fiona
import pandas as pd
import shapely
import os
import pathlib
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from textwrap import wrap
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import matplotlib.colors as colors
import numpy as np
import seaborn as sns
import matplotlib.ticker as mtick
# %% Clip CDL and write to CSV

class CDLClip:
    def __init__(self, ClipPath, ClipName, CDLFolder, CDLClipOut, MetricsFolder, LookupTablePath, WriteClip, FigFolder):
        self.ClipPath = ClipPath # Set clip file path from argparse
        self.ClipName = ClipName # Set clip name from argparse
        self.CDLFolder = CDLFolder # Set folder path of CDL rasters from argparse
        self.CDLClipOut = CDLClipOut # Set folder path to write clipped CDL tifs from argparse
        self.MetricsFolder = MetricsFolder # Set folder path to write CDL CSVs from argparse
        self.LookupTablePath = LookupTablePath # Set folder path for lookup table
        self.WriteClip = WriteClip # T/F to write clipped tifs
        self.FigFolder = FigFolder # Set folder path for saved figures
        
    def extract(self):
        
        # Get raster filepaths and import clipping files
        AllCDLPaths=[] # Create empty list for paths to CDL rasters
        FileNames=[] # Create empyt list for filenames of CDL rasters
        for subdir,dirs,files in os.walk(self.CDLFolder): # Walk across CDL raster folder
            for file in files: # Loop across files in CDL raster folder
                if file.endswith(".tif"): # Select only .tif files
                    FileNames.append(file) # Append individual files to filename list
                    filepath = subdir+os.sep+file # Concatenate subdir and file name
                    AllCDLPaths.append(filepath) # Append full filepath to All CDLPaths list
        ClipFile = gpd.read_file(self.ClipPath) # read clipping shapefile to variable ClipFile
        
        # Loop across CDL rasters
        for count,value in enumerate(AllCDLPaths): # Loop across CDL raster paths
            CDLName = FileNames[count][0:9] # Extract CDL Name from FileNames list
            CDLYear = FileNames[count][4:8] # Extract CDL year from FileNames list
            ras_fp = Path(value) # Set CDL raster path
            ras = rasterio.open(ras_fp) # Open CDL raster
            rasCRS = ras.crs # Set raster CRS to rasCRS variable
            rasEPSG = ras.crs.to_epsg() # Translate raster CRS to epsg
            ClipCRS = rasterio.crs.CRS.from_user_input(ClipFile.crs) # Translate clip CRS to rasterio format for equality evaluation
            
            # Reprojection routine
            if ClipCRS != rasCRS: # CRS equality evaluation 
                ClipFile = ClipFile.to_crs(rasEPSG) # If CRS not equal, project ClipFile to raster EPSG
            
            ClipFileShape = ClipFile["geometry"] # Pull geometry from clipping file
            ClipArea = ClipFile.area[0] # Compute area of clipping file 
            
            # Clip raster
            out_image, out_transform = rasterio.mask.mask(ras, ClipFileShape, crop=True)
            out_meta = ras.meta    
            out_meta.update({"driver": "GTiff",
                             "height": out_image.shape[1],
                             "width": out_image.shape[2],
                             "transform": out_transform})
            # Clipped raster write out routine
            if self.WriteClip==True:
                os.chdir(self.CDLClipOut)
                ClipTifName = CDLName + self.ClipName + '.tif'
                with rasterio.open(ClipTifName, "w", **out_meta) as dest:
                    dest.write(out_image)
                print("Wrote ",ClipTifName," to folder ",self.CDLClipOut)
            
            values, counts = np.unique(out_image, return_counts=True) # Count unique values in raster

            # Create dataframe to hold count, value information
            counts = counts.transpose()
            values = values.transpose()
            CDL_DF = pd.DataFrame(counts)
            CDL_DF['CDL_CODE']=values
            CDL_DF = CDL_DF.rename(columns={0:'Count'})
            
            # Read lookup table between CDL codes and class names into dataframe
            CDL_LOOKUP = pd.read_csv(self.LookupTablePath)
            CDL_LOOKUP = CDL_LOOKUP.rename(columns={'Codes':'CDL_CODE'})

            # Join lookup table and count/value dataframe
            CDL_DF = CDL_DF.merge(CDL_LOOKUP, on='CDL_CODE')
            RasDim = np.absolute(ras.transform[0]*ras.transform[4]) # Calculate area of raster pixel in native units
            CDL_DF['Area']= CDL_DF['Count']*(RasDim)
            CDL_DF['AreaUnits'] = ras.crs.linear_units + "^2"
            CDL_DF['PercentArea']=CDL_DF['Area']/ClipArea
            CDL_DF['Year']= CDLYear
            CDL_DF = CDL_DF.loc[CDL_DF['CDL_CODE']!=0]
            Check = CDL_DF['PercentArea'].sum(axis=0)
            print("Total area percentage = ",Check)
            os.chdir(self.MetricsFolder)
            CDL_DF = CDL_DF.sort_values('PercentArea',ascending=False)
            CDL_DF_Name = CDLName + self.ClipName + '.csv'
            CDL_DF.to_csv(CDL_DF_Name,index=False)
            aggregation_functions = {'Count':'sum','Area': 'sum', 'PercentArea': 'sum', 'CDL_CODE': 'first','Class_Names':'first','CombineClassNames':'first',
                                     'AreaUnits':'first','Year':'first'}
            CDL_DF_Combined = CDL_DF.groupby(CDL_DF['CombineClassNames']).aggregate(aggregation_functions)
            CDL_DF_Combined = CDL_DF_Combined.drop(['CombineClassNames'],axis=1)
            #CDL_DF_Combined = CDL_DF_Combined.drop(columns=CDL_DF_Combined.columns[1])
            CDL_DF_NameCombined = CDLName + self.ClipName + '_Combined.csv'
            CDL_DF_Combined = CDL_DF_Combined.sort_values('PercentArea',ascending=False)
            #CDL_DF_Combined = CDL_DF_Combined.reset_index()
            CDL_DF_Combined.to_csv(CDL_DF_NameCombined)
            print("Wrote ", CDL_DF_Name, " to folder ",self.MetricsFolder)
            print("Wrote ", CDL_DF_NameCombined, " to folder ",self.MetricsFolder)
            #return(CDL_DF)
    
    def plotCDL(self):
        AllCSVPaths=[]
        FileNames=[]
        self.AllData = pd.DataFrame()
        for subdir,dirs,files in os.walk(self.MetricsFolder):
            for file in files:
                if file.endswith("Combined.csv"):
                    FileNames.append(file)
                    filepath = subdir+os.sep+file
                    AllCSVPaths.append(filepath)
        for count,value in enumerate(AllCSVPaths):
            data = pd.read_csv(value)
            self.AllData = pd.concat([self.AllData,data])
        self.AllData.reset_index()
        self.AllData['Year'] = pd.to_datetime(self.AllData['Year'],format='%Y')
        PlotName = self.ClipName + " Landcover"
        sns.set_theme(style="darkgrid",rc={"axes.linewidth": 2, "axes.edgecolor":".15"})
        sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5,"lines.markersize":12})
        fig,ax = plt.subplots(figsize=(8,6))
        sns.lineplot(data=self.AllData, x='Year',y='PercentArea',palette="tab10",
                     hue='CombineClassNames',style='CombineClassNames',markers=True,
                     dashes=True,ax=ax).set(title=PlotName)
        ax.legend(loc="right")
        ax.set_ylabel("% of watershed area")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
        ax.set_xlabel("")
        sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
        os.chdir(self.FigFolder)
        fig.savefig(PlotName,dpi=300,bbox_inches='tight')
        return(self.AllData)
    
# %% Test Function 

# DornQ_ClipPath = Path(r'C:\Users\cjr2\Documents\GISData\DornCreek\GageQWatershed.shp')
# DornQ_CDLFolder = Path(r'G:\NASS')
# DornQ_ClipName = "DornQ_05427927"
# DornQ_OutFolder = Path(r'C:\Users\cjr2\Documents\GISData\DornCreek\CDL')      
# DornQ_CDLClipFolder = Path(r'G:\NASS\ClipTemp')           
# DornQ_LookupTablePath = Path(r'C:\Users\cjr2\Documents\GISData\LandCover\WI_CDL_2018\WI_CDL_2018\CDLCodeLookupCombine.csv')           
# DornQ_WriteClip = False
# FigFolder = Path(r'C:\Users\cjr2\Documents\GISData\DornCreek\Figures')     

# DornQCDL = CDLClip(DornQ_ClipPath,DornQ_ClipName,DornQ_CDLFolder,
#                    DornQ_CDLClipFolder,DornQ_OutFolder,DornQ_LookupTablePath,
#                    DornQ_WriteClip,FigFolder)
# DornQCDL.extract()     
# DornQData = DornQCDL.plotCDL()  

