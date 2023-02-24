# CDLExtract
Function that extracts Cropland Data Layer (CDL) statistics for all available years for an arbitrary shapefile

CDLClip(ClipPath, ClipName, CDLFolder, CDLClipOut, MetricsFolder, LookupTablePath, WriteClip)

ClipPath = Path to clipping shapefile
CDLFolder = Cropland Data Layer raster folder
CDLClipOut = Cropland Data Layer clipped files write folder
MetricsFolder = Metrics CSV write folder
LookupTablePath = Path to lookup CSV
WriteClip = Boolean, write out clipped rasters or do not
FigFolder = Figure write folder

# Example
DornQ_ClipPath = Path(r'C:\Users\cjr2\Documents\GISData\DornCreek\GageQWatershed.shp')
DornQ_CDLFolder = Path(r'G:\NASS')
DornQ_ClipName = "DornQ_05427927"
DornQ_OutFolder = Path(r'C:\Users\cjr2\Documents\GISData\DornCreek\CDL')      
DornQ_CDLClipFolder = Path(r'G:\NASS\ClipTemp')           
DornQ_LookupTablePath = Path(r'C:\Users\cjr2\Documents\GISData\LandCover\WI_CDL_2018\WI_CDL_2018\CDLCodeLookupCombine.csv')           
DornQ_WriteClip = False      

DornQCDL = CDLClip(DornQ_ClipPath,DornQ_ClipName,DornQ_CDLFolder,
                   DornQ_CDLClipFolder,DornQ_OutFolder,DornQ_LookupTablePath,
                   DornQ_WriteClip)
DornQCDL.extract()     
DornQData = DornQCDL.plotCDL()  
![DornQ_05427927 Landcover](https://user-images.githubusercontent.com/45494890/221284991-c0d3fd89-72dc-4fda-91c8-6744f8d11e7d.png)
