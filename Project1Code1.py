#Cell Tower Python Code
#By Josh Alpers and Ryan Egbert

# Import arcpy module
import arcpy
from arcpy.sa import *
import os
# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
# Local variables:
utah_ned30 = arcpy.GetParameterAsText(0) 
arcpy.AddMessage(utah_ned30)
Cellular_Towers = arcpy.GetParameterAsText(1)
counties = arcpy.GetParameterAsText (2)
counties_name = arcpy.GetParameterAsText(3) 
Highways = arcpy.GetParameterAsText(4)
Geodatabase = arcpy.GetParameterAsText(5)
Output_Coordinate_System = arcpy.GetParameterAsText(6)
cellsize_option = arcpy.GetParameterAsText(7)  
Acceptable_Slope_List = arcpy.GetParameterAsText(8)
template_layer = arcpy.GetParameterAsText(9)
output_folder = arcpy.GetParameterAsText(10)
raster_symbology = arcpy.GetParameterAsText(11)
# Environment Settings
arcpy.env.outputCoordinateSystem = Output_Coordinate_System
arcpy.env.overwriteOutput = True
arcpy.env.workspace = Geodatabase
arcpy.env.cellSize = cellsize_option
# Define Global Variables
layer_counties = arcpy.mapping.Layer(counties)
new_county = "County_Boundary"
county_names = [] 
county_string = counties_name.replace("'","")
counties_array = county_string.split(';')
County_Buffer = 'County_Buffer'
Cellular_Projected_Clip = 'Cellular_Projected_Clip'
Suitable_Slope = 'Suitable_Slope'
Highways_Buffer = 'Highways_Buffer'
Access_Roads_Buffer = 'Access_Roads_Buffer'
County_Raster = 'County_Raster'
for county in counties_array:
	county_names.append(county)
# Count the number of counties in row for how many maps we need to create
total_counties = len(county_names)
#Gets the acceptable slope from the comma delineated list
Acceptable_Slope = Acceptable_Slope_List.split(";")
total_slopes = len(Acceptable_Slope)
slopes = [int(x) for x in Acceptable_Slope]
all_counties = [str(x) for x in county_names]
#Calculate Total Number of Pages
total_pages = total_counties * total_slopes
arcpy.AddMessage('There will be ' + str(total_pages) + ' pages in this Atlas')
arcpy.AddMessage('The following counties and slopes will be included:')
for i in range(0,total_counties):
	for j in range(0,total_slopes):
		county_slope_nexus = str(all_counties[i]) + " County, Slope of " + str(slopes[j])
		arcpy.AddMessage(county_slope_nexus)

		##Step 1: Setting up the loop
arcpy.AddMessage('Step 1: Setting up for the Loop')
## Set up Page Numbers
Page_Numbers = 0
## Specify path to where you will save the PDF
arcpy.AddMessage('-pdf_path =' + output_folder + '\\AtlasCounties.pdf')
pdf_path = output_folder + "\\AtlasCounties.pdf"
## if an atlas already exists, remove it
arcpy.AddMessage('-Creating New Atlas')
if os.path.exists(pdf_path):
	os.remove(pdf_path)
##Create the atlas PDF file
pdf_doc = arcpy.mapping.PDFDocumentCreate(pdf_path)
## Specify Current map document and data frame
arcpy.AddMessage('-Specify the Current map Document and Data Frame')
mxd = arcpy.mapping.MapDocument ("CURRENT")
cdf = arcpy.mapping.ListDataFrames(mxd, "County Map")[0] #Main data frame
# A list to dynamically populate the county names
arcpy.AddMessage('-Create a list to dynamically populate the county names and count them')
#rows = arcpy.SearchCursor(layer_counties, "", "", counties_name, counties_name + " A")
# Create function county_analysis
def county_analysis(county_select):
	## Note the '[0]' represents that the input to the tool is optional
	# Part 1
	# Select, Buffer, Clip, Kernel Density, and Raster Calculator
	arcpy.AddMessage ('Part 1: Select, Buffer, Clip, Kernel Density, and Raster Calculator')
	## Select County Polygons
	## (Input, Output, SQL Statement)
	arcpy.AddMessage('-Select(' + str(county_select) +' County) Tool Running')
	arcpy.Select_analysis(layer_counties, new_county, '"' + 'NAME' + "\" = '" + county_select + "'")
	## Buffer County Polygons## (Input Feature, Output Feature,  Distance: Linear Unit, Side Type [0]
	## End Type [0], Dissolve Type [0], Dissolve Fields [0])
	arcpy.AddMessage ('-Buffer (' + str(county_select) +' County) Tool Running')
	arcpy.Buffer_analysis (new_county, County_Buffer, '50 Miles', 'FULL', 'ROUND', 'ALL','')
	## Clip Cell Tower With County Buffer:
	## (Input Features, Clip Features, Output Feature Class, XY Tolerance [0])
	arcpy.AddMessage('-Clip Tool Running')
	arcpy.Clip_analysis(Cellular_Towers, County_Buffer, Cellular_Projected_Clip, '')
	## Clip Utah State Raster With County Buffer:
	## (Input Features, Clip Features, Output Feature Class, XY Tolerance [0])
	arcpy.AddMessage('-Clip ' + str(county_select) +' Raster')
	arcpy.Clip_management(utah_ned30, '221456 4668373 678243 4081000', County_Raster, new_county, '0', 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')
	##kernel Density tool with Cellular_Projected_Clip
	## (input Feature, Population Field, Output Cell Size [0],
	## Search Radius [0], Area Units [0])
	arcpy.AddMessage('-Kernel Density Tool Running')
	Kernel_DEM = KernelDensity(Cellular_Projected_Clip, 'NONE', cellsize_option, '20000', 'SQUARE_KILOMETERS')
	## Raster Calculator for Kernel Density:
	## (Map Algebra Expression)
	arcpy.AddMessage('-Calculating Appropriate Tower Density')
	TowerDensityDEM = LessThan(Kernel_DEM * 10000, 20)
	TowerDensityDEM.save('TowerDensityDEM')
	#Part 2
	#Slope and Raster Calculator
	arcpy.AddMessage('Part 2; Slope and Raster Calculator')
	## Slope of County Rasters
	## This takes the DEM file(s) and creates the slope throughout the given file
	## (Input Raster, Output Measurement [0], Z Factor [0])
	arcpy.AddMessage('-Slope Tool Running')
	Slope_DEM = Slope(County_Raster, 'DEGREE', '1')
	Slope_DEM.save('Slope_DEM')
	
#Create function slope_analysis	
def slope_analysis(slope_single):
	## Find Suitable_Slope
	arcpy.AddMessage('-Calculating Appropriate Slope')
	Suitable_Slope = LessThan('Slope_DEM', slope_single) ##This is the input that we want to be able to change/adjust
	# Part 3
	# Buffer, Extract, by Mask, and Raster Calculator
	arcpy.AddMessage ('Part 3: Buffer, Extract by Mask, and Raster Calculator')
	## (Input Feature, Output Feature, Distance : Linear Unit, Side Type [0],
	## End Type [0], Dissolve Type [0], Dissolve Fields [0])
	arcpy.AddMessage ('-buffer (' + str(Highways) + ') Tool Running')
	arcpy.Buffer_analysis(Highways, Highways_Buffer, '2 Kilometers', 'FULL', 'ROUND', 'ALL', '')
	#Delete Code Below
	#arcpy.AddMessage ('-buffer (' + str(Access_Roads) + ') Tool Running')
	#arcpy.Buffer_analysis(Highways, Access_Roads_Buffer, '0.1 Kilometers', 'FULL', 'ROUND', 'ALL', '')
	#arcpy.Erase_analysis(Highways_Buffer, Access_Roads_Buffer, Final_Buffer, '')
	## Extract by Mask Highways with SuitableSlope
	## (Input Raster, Feature Mask Data)
	arcpy.AddMessage('-Extract by Mask Tool Running')
	SuitableSlopebyRoads = ExtractByMask(Suitable_Slope, Highways_Buffer)
	## Raster Calculator for SuitableSlopebyRoads and TowerDensityDEM
	arcpy.AddMessage ('-Calculating Suitable Cell Tower Sites')
	Final_Suitability_Sites = SuitableSlopebyRoads * 'TowerDensityDEM'
	Final_Suitability_Sites.save('Final_Suitability_Sites1')
	#Add Final_Suitability_Sites to Map
	arcpy.AddMessage('-Add Final_Suitability_Sites to Map as a Layer')
	mxd = arcpy.mapping.MapDocument('CURRENT')
	df = arcpy.mapping.ListDataFrames(mxd, 'County Map')[0]
	arcpy.MakeRasterLayer_management('Final_Suitability_Sites1', 'Final_Suitability_Sites')
	newlayer = arcpy.mapping.Layer('Final_Suitability_Sites')
	arcpy.ApplySymbologyFromLayer_management(newlayer, raster_symbology)
	arcpy.mapping.AddLayer(df, newlayer, 'TOP')
	arcpy.RefreshActiveView()
	mxd.save
	arcpy.AddMessage('Final Suitability Sites Layer Added')

# Create pdf_maker
def pdf_maker(county_select, page, pdfdoc, slope_pdf):
	# Step 4: Creating the Atlas maps Beginning of PDF
	arcpy.AddMessage('Step 4: Creating the Atlas Maps')
	arcpy.AddMessage("-Current iteration = " + str(i+1) + "of" + str(total_counties))
	arcpy.AddMessage("-Current counties = " + county_select.capitalize())
	#Check for and delete any previous county file
	pdf_county = str(output_folder + "\\" + county_select.capitalize() + ".pdf")
	if os.path.exists(pdf_county):
		os.remove(pdf_county)
	#Select the current county
	arcpy.AddMessage('--Selecting ' + county_select.capitalize())
	arcpy.Select_analysis(layer_counties, new_county, '"' + 'NAME' + "\" = '" + county_select + "'")
	layer_new_county = arcpy.mapping.Layer(new_county)
	#Adding Layer to Map
	arcpy.AddMessage('--Adding Layer to Map')
	arcpy.mapping.AddLayer(cdf, layer_new_county, "TOP")
	arcpy.RefreshActiveView()
	# *Editing Title and Page Number and Slope
	arcpy.AddMessage('--*Editing Title and Page Number')
	for elem in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
		if elem.text == "<FNT size='36'>TITLE</FNT>":
			elem.text = "<FNT size='36'>" + county_select + " COUNTY</FNT>"
		if elem.text == "<FNT size='30'>PAGE</FNT>":
			elem.text = "<FNT size='30'>" +str(page) + " of " + str(total_pages) + "</FNT>"
		if elem.text == "<FNT size='30'>SLOPE</FNT>":
			elem.text = "<FNT size='30'>" + "Slope = " + str(slope_pdf) + "</FNT>"
	arcpy.RefreshActiveView()
	# Zoom to the new layer in the active frame
	arcpy.AddMessage('--Zoom to Layer')
	arcpy.SelectLayerByAttribute_management(new_county, "NEW_SELECTION")
	cdf.zoomToSelectedFeatures()
	arcpy.SelectLayerByAttribute_management(new_county, "CLEAR_SELECTION")
	arcpy.RefreshActiveView()
	# Apply common symbols from a layer
	arcpy.AddMessage('--changing Symbology of Layer')
	arcpy.ApplySymbologyFromLayer_management(new_county, template_layer)
	arcpy.SelectLayerByAttribute_management(new_county, "CLEAR_SELECTION")
	arcpy.SelectLayerByAttribute_management(template_layer, "CLEAR_SELECTION")
	arcpy.SelectLayerByAttribute_management(layer_counties, "CLEAR_SELECTION")	
	arcpy.RefreshActiveView()
	# Give ArcMap a little time to process
	for j in range(500):
		pass
	# Export map to PDF
	arcpy.AddMessage('--Export Map to PDF and Append to Atlas')
	arcpy.mapping.ExportToPDF(mxd,pdf_county)
	# Add county map to atlas
	pdfdoc.appendPages(pdf_county)
	# Reset Title and Page Number and Slope
	arcpy.AddMessage('Reset Title and Page Number')
	for elem in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
		if elem.text == "<FNT size='36'>" + county_select + " COUNTY</FNT>":
			elem.text = "<FNT size='36'>TITLE</FNT>"
		if elem.text == "<FNT size='30'>" +str(page) + " of " + str(total_pages) + "</FNT>":
			elem.text = "<FNT size='30'>PAGE</FNT>"
		if elem.text == "<FNT size='30'>" + "Slope = " + str(slope_pdf) + "</FNT>":
			elem.text = "<FNT size='30'>SLOPE</FNT>"
	# Remove intermediate layers and refresh
	arcpy.AddMessage('--Remove intermediate layers and refresh')
	arcpy.mapping.RemoveLayer(cdf, layer_new_county)
	arcpy.Delete_management(new_county)
	arcpy.RefreshActiveView()

# Run Loops	
for county in county_names:
	arcpy.AddMessage('County = ' + str(county))
	county_analysis(county);
	
	for slope in slopes:
		arcpy.AddMessage('Slope = ' + str(slope))
		slope_analysis(slope);
		#Update Page Number
		Page_Numbers = Page_Numbers + 1
		pdf_maker(county, Page_Numbers, pdf_doc, slope);

# end of PDF
# Save PDF and Close
arcpy.AddMessage('End of Loop')
arcpy.AddMessage('Saving and Closing')
pdf_doc.saveAndClose()		
pdf_doc = arcpy.mapping.PDFDocumentOpen(pdf_path)