from django.http import HttpResponse, HttpResponseRedirect
from webservices.models import *
import json
import sys
import os
from django.db import connection as con
from webservices.SampleQuery import *
from webservices.utility import *
from django.shortcuts import render, render_to_response
from webservices.json2kml import *
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
#direct stdout to stderr so that it is logged by the webserver
sys.stdout = sys.stderr

#Function to format oxides by subscripting digits
def formatOxide(species):
        retStr=""
        i=0
        while(i<len(species)):
                if species[i].isdigit():
                        retStr+='<sub>'+species[i]+'</sub>'
                else:
                        retStr+=species[i]
                i+=1
        return retStr


#Request to serve search.html
def search(request):
	return render(request, 'index.html')

def samples(request):
	samples_data=[]
	samples=Samples.objects.filter(public_data='Y')|Samples.objects.filter(user_id='139')
	i=0
	for sample in samples:
		#initialize the variables
		sample_data={}
		sample_latlon=""
		sample_number=""
		sample_metamorphic_regions=[]
        	sample_country=""
        	sample_owner=""
        	sample_rock_type=""
        	sample_metamorphic_grades=[]
		sample_minerals=[]
		sample_regions=[]
		sample_reference_first_authors=[]
		sample_reference_journal_names=[]
		sample_reference_publication_years=[]
		sample_number_link=""
		sample_id=""

		#get sample id
		sample_id=sample.sample_id
		
		#get sample metamorphic regions
		samplemetamorphicregions=sample.samplemetamorphicregionsdup_set.all()
		for samplemetamorphicregion in samplemetamorphicregions:
			sample_metamorphic_regions.append(samplemetamorphicregion.metamorphic_region.name)
		
		#get lat lon from location
		
		sample_location_x=Samples.objects.raw('select sample_id,st_X(location) as geo from samples where sample_id='+str(sample.sample_id))[0].geo
		sample_location_y=Samples.objects.raw('select sample_id,st_Y(location) as geo from samples where sample_id='+str(sample.sample_id))[0].geo
		sample_latlon=str(sample_location_y)+","+str(sample_location_x)
		
		'''
		sample_latlon=Samples.objects.raw('select sample_id,substr(ST_asText(location), 7) as geo from samples where sample_id='+str(sample.sample_id))[0].geo
		sample_latlon=sample_latlon.rstrip(')')
		sample_latlon=sample_latlon.replace(' ',',')		
		'''
		
		#get sample number
		sample_number=sample.number

		#get sample country
		sample_country=sample.country
		
		#get sample owner
		sample_owner=sample.user.name

		#get sample rock type
		sample_rock_type=sample.rock_type.rock_type

		#get sample metamorphic grades
		samplemetamorphicgrades=sample.samplemetamorphicgradesdup_set.all()
		for samplemetamorphicgrade in samplemetamorphicgrades:
			sample_metamorphic_grades.append(samplemetamorphicgrade.metamorphic_grade.name)
		
		#get sample minerals
		sampleminerals=sample.samplemineralsdup_set.all()
		for samplemineral in sampleminerals:
			sample_minerals.append(samplemineral.mineral.name)

		#get sample regions
		sampleregions=sample.sampleregionsdup_set.all()
		for sampleregion in sampleregions:
			sample_regions.append(sampleregion.region.name)

		#get sample references
		samplereferences=sample.samplereferencedup_set.all()
		for samplereference in samplereferences:
			referencenumber=samplereference.reference.name
			georeferences=Georeference.objects.filter(reference_number=str(referencenumber))
			for georeference in georeferences:
				sample_reference_first_authors.append(georeference.first_author)
				sample_reference_journal_names.append(georeference.journal_name_2)
				sample_reference_publication_years.append(georeference.publication_year)
	
		#url to metpetdb
                sample_link='http://metpetdb.rpi.edu/metpetweb/#sample/'+str(sample_id)
		
		sample_data["sample_id"]=sample_id
		sample_data["label"]=sample_number
		sample_data['sample_link']=sample_link
		sample_data["sample_metamorphic_regions"]=sample_metamorphic_regions
		sample_data["sample_country"]=sample_country
		sample_data["sample_owner"]=sample_owner
		sample_data["sample_rock_type"]=sample_rock_type
		sample_data["sample_metamorphic_grades"]=sample_metamorphic_grades
		sample_data["sample_minerals"]=sample_minerals
		sample_data["sample_regions"]=sample_regions
		sample_data["sample_reference_first_authors"]=sample_reference_first_authors
		sample_data["sample_reference_journal_names"]=sample_reference_journal_names
		sample_data['sample_reference_publication_years']=sample_reference_publication_years
		sample_data["sample_latlon"]=sample_latlon
		samples_data.append(sample_data)
		
	return HttpResponse("{\"items\":"+json.dumps(samples_data)+"}")

def chemical_analyses(request):
	from django.db import connection
	chemical_analyses_data=[]
	#chemical_analyses=ChemicalAnalyses.objects.filter(public_data='Y')|ChemicalAnalyses.objects.filter(user_id='139')
	
	chemical_analyses=ChemicalAnalyses.objects.raw("select * from chemical_analyses where (public_data='Y' or user_id='139') and (large_rock='Y' or mineral_id is not null)");

	id=0
	i=0
	for chemical_analysis in chemical_analyses:
		chemical_analysis_data={}
		chemical_analysis_id=""
		chemical_analysis_large_rock=""
		chemical_analysis_count=""
		chemical_analysis_mineral_name=""
		chemical_analysis_owner=""
		chemical_analysis_rock_type=""
		chemical_analysis_metamorphic_grade=[]
		chemical_analysis_metamorphic_regions=[]
		chemical_analysis_method=""
		chemical_analysis_first_authors=[]
		chemical_analysis_publication_journal_names=[]
		chemical_analysis_publication_years=[]
		chemical_analysis_total_weight=""
		chemical_analysis_elements=[]
		chemical_analysis_oxides=[]
		chemical_analysis_latlon=""
		chemical_analysis_sample_number=""
		chemical_analysis_sample_id=""
		sample_minerals=[]

		#get chemical analysis id
		chemical_analysis_id=chemical_analysis.chemical_analysis_id

		#get chemical analysis sample id
                chemical_analysis_sample_id=chemical_analysis.subsample.sample.sample_id

		#get chemical analyses count
	        cursor=con.cursor()
        	cursor.execute('select count(chemical_analysis_id) from chemical_analyses where subsample_id='+str(chemical_analysis_sample_id))
        	row=cursor.fetchone()
		chemical_analysis_count=row[0]
		
		#get lat lon from location
                sample_location_x=Samples.objects.raw('select sample_id,st_X(location) as geo from samples where sample_id='+str(chemical_analysis_sample_id))[0].geo
                sample_location_y=Samples.objects.raw('select sample_id,st_Y(location) as geo from samples where sample_id='+str(chemical_analysis_sample_id))[0].geo
                chemical_analysis_latlon=str(sample_location_y)+","+str(sample_location_x)

		#get chemical analysis large rock
		chemical_analysis_large_rock=chemical_analysis.large_rock
		
		#get chemical analysis mineral name
		if chemical_analysis_large_rock=='Y' and chemical_analysis.mineral==None:
			chemical_analysis_mineral_name='Bulk Rock'
		elif chemical_analysis_large_rock=='N' and chemical_analysis.mineral!=None:
			chemical_analysis_mineral_name=chemical_analysis.mineral.name
		elif chemical_analysis_large_rock=='N' and chemical_analysis.mineral==None:
			chemical_analysis_mineral_name=None

		#get chemical analysis method
		chemical_analysis_method=chemical_analysis.analysis_method

		#get chemical analysis owner
		chemical_analysis_owner=chemical_analysis.user.name

		#get chemical analysis total weight
		chemical_analysis_total_weight=chemical_analysis.total

		#get chemical analysis oxides
		chemicalanalysisoxides=chemical_analysis.chemicalanalysisoxidesdup_set.all()
		for chemicalanalysisoxide in chemicalanalysisoxides:
			chemical_analysis_oxides.append(formatOxide(str(chemicalanalysisoxide.oxide.species)))
		
		#get chemical analysis elements
		chemicalanalysiselements=chemical_analysis.chemicalanalysiselementsdup_set.all()
		for chemicalanalysiselement in chemicalanalysiselements:
			chemical_analysis_elements.append(chemicalanalysiselement.element.name)

		#get chemical analysis rock type
		chemical_analysis_rock_type=chemical_analysis.subsample.sample.rock_type.rock_type
		
		#get chemical analysis metamorphic grade
		samplemetamorphicgrades=chemical_analysis.subsample.sample.samplemetamorphicgradesdup_set.all()
		for samplemetamorphicgrade in samplemetamorphicgrades:
			chemical_analysis_metamorphic_grade.append(samplemetamorphicgrade.metamorphic_grade.name)
		#get chemical analysis metamorphic regions
                samplemetamorphicregions=chemical_analysis.subsample.sample.samplemetamorphicregionsdup_set.all()
                for samplemetamorphicregion in samplemetamorphicregions:
                        chemical_analysis_metamorphic_regions.append(samplemetamorphicregion.metamorphic_region.name)
			
		#get chemical analysis references
		chemicalreferences=chemical_analysis.subsample.sample.samplereferencedup_set.all()
		for chemicalreference in chemicalreferences:
			referencenumber=chemicalreference.reference.name
			georeferences=Georeference.objects.filter(reference_number=str(referencenumber))
			for georeference in georeferences:
				chemical_analysis_first_authors.append(georeference.first_author)
				chemical_analysis_publication_journal_names.append(georeference.journal_name_2)
				chemical_analysis_publication_years.append(georeference.publication_year)
		
		#get chemical analysis sample number
		chemical_analysis_sample_number=chemical_analysis.subsample.sample.number

		#get sample minerals
		sampleminerals=SampleMineralsDup.objects.raw('select * from sample_minerals_dup where sample_id='+str(chemical_analysis_sample_id))
		for samplemineral in sampleminerals:
                        sample_minerals.append(samplemineral.mineral.name)


		#url to metpetdb
		chemical_analysis_link="http://metpetdb.rpi.edu/metpetweb/#sample/"+str(chemical_analysis_sample_id)

		chemical_analysis_data['chemical_analysis_id']=chemical_analysis_id
		chemical_analysis_data['sample_id']=chemical_analysis_sample_id
		chemical_analysis_data['label']=chemical_analysis_sample_number
		chemical_analysis_data['chemical_analysis_link']=chemical_analysis_link
		chemical_analysis_data['chemical_analysis_count']=chemical_analysis_count
		chemical_analysis_data['chemical_analysis_latlon']=chemical_analysis_latlon
		chemical_analysis_data['chemical_analysis_large_rock']=chemical_analysis_large_rock
		chemical_analysis_data['chemical_analysis_mineral_name']=chemical_analysis_mineral_name
		chemical_analysis_data['chemical_analysis_method']=chemical_analysis_method
		chemical_analysis_data['chemical_analysis_owner']=chemical_analysis_owner
		chemical_analysis_data['chemical_analysis_total_weight']=chemical_analysis_total_weight
		chemical_analysis_data['chemical_analysis_oxides']=chemical_analysis_oxides
		chemical_analysis_data['chemical_analysis_elements']=chemical_analysis_elements
		chemical_analysis_data['chemical_analysis_rock_type']=chemical_analysis_rock_type
		chemical_analysis_data['chemical_analysis_metamorphic_grade']=chemical_analysis_metamorphic_grade
		chemical_analysis_data['chemical_analysis_metamorphic_regions']=chemical_analysis_metamorphic_regions
		chemical_analysis_data['chemical_analysis_first_authors']=chemical_analysis_first_authors
		chemical_analysis_data['chemical_analysis_publication_journal_names']=chemical_analysis_publication_journal_names
		chemical_analysis_data['chemical_analysis_publication_years']=chemical_analysis_publication_years
		chemical_analysis_data['chemical_analysis_sample_minerals']=sample_minerals
		chemical_analyses_data.append(chemical_analysis_data)

	return HttpResponse("{\"items\":"+json.dumps(chemical_analyses_data)+"}")

'''S2S webservice view'''
#Main faceted serach view
def metpetdb(request):

	formattype=request.GET.get('format','json')

	returntype=request.GET.get('returntype','sampleresults')
	
	rocktype_id=request.GET.get('rocktype_id','')
	
	country=request.GET.get('country_name','')
	
	owner_id=request.GET.get('owner_id','')
	
	mineral_id=request.GET.get('mineral_id','')
	#print mineral_id

	mineral2_id=request.GET.get('mineral2_id','')
	#print mineral2_id
	
	region_id=request.GET.get('region_id','')

	metamorphic_grade_id=request.GET.get('metamorphicgrade_id','')
	
	metamorphic_region_id=request.GET.get('metamorphicregion_id','')

	publication_id= request.GET.get('publication_id','')
	
	if rocktype_id!='':
		rocktype_id_list=rocktype_id.split(',')
	else:
		rocktype_id_list=[]

	if mineral_id!='':
		mineral1_id_list=mineral_id.split(',')
	else:
		mineral1_id_list=[]

	if mineral2_id!='':
		mineral2_id_list=mineral2_id.split(',')
	else:
		mineral2_id_list=[]
	
	if owner_id!='':
		owner_id_list=owner_id.split(',')
	else:
		owner_id_list=[]
	
	if country!='':
		country_list=country.split(',')
	else:
		country_list=[]

	if region_id!='':
		region_id_list=region_id.split(',')
	else:
		region_id_list=[]
	
	if metamorphic_region_id!='':
		metamorphic_region_id_list=metamorphic_region_id.split(',')
	else:
		metamorphic_region_id_list=[]

	if metamorphic_grade_id!='':
		metamorphic_grade_id_list=metamorphic_grade_id.split(',')
	else:
		metamorphic_grade_id_list=[]
	
	if publication_id!='':
		publication_id_list=publication_id.split(',')
	else:
		publication_id_list=[]
		
	#mineral facet assemblage is a list of lists

	mineral_id_list =[]
	mineral_id_list.append(mineral1_id_list)
	mineral_id_list.append(mineral2_id_list)


	samples=SampleQuery(rock_type=rocktype_id_list,country=country_list,owner_id=owner_id_list,mineral_id=mineral_id_list,region_id=region_id_list,metamorphic_grade_id=metamorphic_grade_id_list, metamorphic_region_id=metamorphic_region_id_list, publication_id=publication_id_list)
	#print samples
	#sample_test = SampleQuery(rock_type=[], country=[], owner_id=[], mineral_id=[], region_id=[], metamorphic_grade_id=[13,], metamorphic_region_id=[], publication_id=[])

	if returntype=='rocktype_facet':
		return HttpResponse(getFacetJSON(samples.rock_type_facet()), content_type="application/json")
	elif returntype=='country_facet':
		return HttpResponse(getFacet(samples.country_facet()), content_type="application/json")
	elif returntype=='mineral_facet':
		return HttpResponse(getFacetJSON(samples.mineral_facet()), content_type="application/json")
	elif returntype=='mineral2_facet':
		return HttpResponse(getFacetJSON(samples.mineral_facet2()), content_type="application/json")
	elif returntype=='region_facet':
		return HttpResponse(getFacetJSON(samples.region_facet()), content_type="application/json")
	elif returntype=='owner_facet':
		return HttpResponse(getFacetJSON(samples.owner_facet()), content_type="application/json")
	elif returntype=='metamorphicgrade_facet':
		return HttpResponse(getFacetJSON(samples.metamorphic_grade_facet()), content_type="application/json")
	elif returntype=='metamorphicregion_facet':
		return HttpResponse(getFacetJSON(samples.metamorphic_region_facet()), content_type="application/json")
	elif returntype== 'publication_facet':
		return HttpResponse(getFacetJSON(samples.publication_facet()), content_type="application/json")
	elif returntype=='map':
		return HttpResponse(getAllJSON(samples.get_main_brief()), content_type="application/json")
	else:
		cursor=con.cursor()
        cursor.execute(samples.get_count())
        sample_count=cursor.fetchall()
        #this is currently a hack to pass a html element containing the sample_count
        htmlCount="<div id='sampleCount' display:'none'>"+str(sample_count[0][0])+"</div>"
        #print htmlCount
        if sample_count>500:
        	return HttpResponse(getSampleResults(samples.get_main(500))+htmlCount)
        else:
        	return HttpResponse(getSampleResults(samples.get_main(500)))
	
'''
def earth(request):
		PROJECT_DIR = os.path.dirname(__file__)
		PROJECT_DIR = os.path.join(PROJECT_DIR, '..')
		KML_DIR = os.path.join(PROJECT_DIR, 'web')
		data = request.POST.get('jsondata')
		items = json.loads(data)
		f = open(KML_DIR+'/'+'BasicKML.kml','w')
		with open(KML_DIR+'/'+'BasicKML.kml', 'w') as f:
			myfile = File(f)
			myfile.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
			myfile.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
			myfile.write("  <Document>\n")
			for item in items:
				myfile.write("   <Folder>\n")
				myfile.write("    <name>"+item["sample_number"]+"</name>\n")
				myfile.write("     <Placemark>\n")
				myfile.write("     <name>"+item["sample_number"]+"</name>\n")
				myfile.write("      <Description>"+"Rocktype: "+item["rock_type"]+"Owner: "+item["owner"]+"</Description>\n")
				myfile.write("       <Point><coordinates>"+item["lat"]+","+item["lon"]+"</coordinates></Point>\n")
				myfile.write("     </Placemark>\n")
				myfile.write("   </Folder>")
				myfile.write("\n")
			myfile.write("  </Document>\n</kml>\n")
			myfile.closed
			f.closed
			f = open(KML_DIR+'/'+'BasicKML.kml', 'r+')
			x= File(f)
			my_data = x.read()
			print my_data
			x.closed
			f.closed
			response = HttpResponse(content_type='application/vnd.google-earth.kml+xml')
			response['Content-Disposition'] = 'attachment; filename="BasicKML.kml"'
			response.write(file(KML_DIR+'/'+'BasicKML.kml', "rb").read())
		return response
'''