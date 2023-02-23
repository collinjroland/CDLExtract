# -*- coding: utf-8 -*-
"""
Created on Mon Feb 20 08:11:59 2023

@author: cjr2

GeneralCLDExtract.py
Extracts land cover types for a given shapefile from a supplied Cropland Data Layer Raster and writes to CSV, can also export clipped TIFs
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
# %% Clip CDL and write to CSV

class CDLClip:
    def __init__(self, ClipPath, ClipName, CDLFolder, CDLClipOut, MetricsFolder, LookupTablePath, WriteClip):
        #columns = ['Sensor','Date','DOY','DataAvail','DataCondition','MaxConc','MeanConc','MedConc','BloomCond','BloomPerc']
        self.ClipPath = ClipPath # Set clip file path from argparse
        self.ClipName = ClipName # Set clip name from argparse
       #self.CDLFolder = pd.DataFrame(columns=columns) # Create empty dataframe for lake cyanobacterial metrics
        self.CDLFolder = CDLFolder # Set folder path of CDL rasters
        self.CDLClipOut = CDLClipOut # Set folder path to write clipped CDL tifs
        self.MetricsFolder = MetricsFolder # Set folder path to write CDL summary dataframe
        self.LookupTablePath = LookupTablePath # Set folder path for lookup table
        self.WriteClip = WriteClip # T/F to write clipped tifs
        
    def extract(self):
        AllCDLPaths=[]
        FileNames=[]
        for subdir,dirs,files in os.walk(self.CDLFolder):
            for file in files:
                if file.endswith(".tif"):
                    FileNames.append(file)
                    filepath = subdir+os.sep+file
                    AllCDLPaths.append(filepath)
        ClipFile = gpd.read_file(self.ClipPath) # read clipping shapefile to variable
        for count,value in enumerate(AllCDLPaths):
            CDLName = FileNames[count][0:9]
            CDLYear = FileNames[count][4:9]
            ras_fp = Path(value)
            ras = rasterio.open(ras_fp)
            rasCRS = ras.crs
            rasEPSG = ras.crs.to_epsg()
            ClipCRS = rasterio.crs.CRS.from_user_input(ClipFile.crs)
            if ClipCRS != rasCRS:
                ClipFile = ClipFile.to_crs(rasEPSG)
            ClipFileShape = ClipFile["geometry"]
            ClipArea = ClipFile.area[0]
            #ClipArea = ClipFile.sum(axis=0) # Total area m2
            out_image, out_transform = rasterio.mask.mask(ras, ClipFileShape, crop=True)
            out_meta = ras.meta    
            out_meta.update({"driver": "GTiff",
                             "height": out_image.shape[1],
                             "width": out_image.shape[2],
                             "transform": out_transform})        
            if self.WriteClip==True:
                os.chdir(self.CDLClipOut)
                ClipTifName = CDLName + self.ClipName + '.tif'
                with rasterio.open(ClipTiffName, "w", **out_meta) as dest:
                    dest.write(out_image)
                print("Wrote ",ClipTifName," to folder ",self.CDLClipOut)
            
            values, counts = np.unique(out_image, return_counts=True)

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
            os.chdir(OutFolder)
            CDL_DF_Name = CDLName + self.ClipName + '.csv'
            CDL_DF.to_csv(CDL_DF_Name)
            print("Wrote ", CDL_DF_Name, " to folder ",OutFolder)
    
    def plotCDL(self):
        AllCSVPaths=[]
        FileNames=[]
        AllData = []
        for subdir,dirs,files in os.walk(self.OutFolder):
            for file in files:
                if file.endswith(".csv"):
                    FileNames.append(file)
                    filepath = subdir+os.sep+file
                    AllCSVPaths.append(filepath)
        for count,value in enumerate(AllCSVPaths):
            Name = FileNames[count]
            NameSplit = Name.split('.')
            DFName = NameSplit[0]
            data = pd.read_csv(value)
            self.AllData.append(data)
        return(self.AllData)
    
    
# %% Real test 

DornQ_ClipPath = Path(r'C:\Users\cjr2\Documents\GISData\DornCreek\GageQWatershed.shp')
DornQ_CDLFolder = Path(r'G:\NASS')
DornQ_OutFolder = Path(r'C:\Users\cjr2\Documents\GISData\DornCreek\CDL')      
DornQ_CDLClipFolder = Path(r'G:\NASS\ClipTemp')           
DornQ_LookupTablePath = Path(r'C:\Users\cjr2\Documents\GISData\LandCover\WI_CDL_2018\WI_CDL_2018\CDLCodeLookup.csv')           
DornQ_WriteClip=False      

DornQCDL = CDLClip(DornQ_ClipPath,"DornQ_05427927",DornQ_CDLFolder,DornQ_CDLClipFolder,DornQ_OutFolder,DornQ_LookupTablePath,DornQ_WriteClip)
DornQCDL = DornQCDL.extract()     
DornQCDL = DornQCDL.plotCDL()  
