from datetime import date
from dateutil.relativedelta import relativedelta

from lit_reviews.models import (
	SearchConfiguration,
	LiteratureSearch,
	SearchProtocol,
	ExclusionReason,
	SearchParameter,
	ExtractionField,
)

def get_db_search_configurations(db, literature_review):
	search_config = SearchConfiguration.objects.filter(
		database=db,
		literature_review=literature_review,
	).first()
	if search_config:
		paramaters = SearchParameter.objects.filter(
			search_config=search_config,
		).order_by("-name")

		return [f"{param.name}: {param.value}" for param in paramaters]

	else:
		return []

def get_db_info(literature_review, db):
	terms_tuples = list( 
					#set( 

						LiteratureSearch.objects.filter(literature_review=literature_review,
								db=db
						).order_by('term').values_list('term')
					#)
				)
	terms = []
	for tup in terms_tuples:
		terms.append(tup[0])


	print("Terms gotten {0}".format(terms))

	if db.search_strategy:
		search_strategy = [*db.search_strategy.split("|"), *get_db_search_configurations(db, literature_review)]
		search_strategy = [item.strip() for item in search_strategy]

	else:
		search_strategy = [*get_db_search_configurations(db, literature_review)]
	
	if db.url:
		url = db.url
	else:
		url = ""
	
	if db.description:
		description = db.description
	else:
		description = ""

	return {

		"name": db.displayed_name,
		"url": url,
		"description": description,
		"terms": terms,
		"search_strategy": search_strategy
	}





def get_database_list(protocol, ae_and_recall=False):
	if ae_and_recall:
		dbs = protocol.ae_databases_to_search.all()
	else:
		dbs = protocol.lit_searches_databases_to_search.all()

	databases = []
	for db in dbs:
		db_info = get_db_info(protocol.literature_review, db)
		## get terms
		databases.append(db_info)

	return databases


def build_protocol_context(lit_review, report_job):
	from client_portal.models import Project

	protocol = SearchProtocol.objects.get(literature_review=lit_review)
	context = {"search_protocol": {}}
	project = Project.objects.filter(lit_review=lit_review).first()
	
	project_name = project.project_name if project else ""
	cp = {}
	cp['version_number'] = str(report_job.version_number)
	
	if lit_review.client.logo:
		logo_file = lit_review.client.logo.url
		cp['company_logo_link'] =  logo_file
	else:
		cp['company_logo_link'] =  ""

	cp['device_name'] = lit_review.device.name if lit_review.device else project_name
	cp['device_classification'] = lit_review.device.classification if lit_review.device else ""
	cp['company_name'] = lit_review.client.name 
	cp['company_address'] = lit_review.client.full_address_string 

	today = date.today().strftime('%b %d, %Y')
	cp['prepared_date'] = str(today).replace(", ", ",")

	cp['preparer'] = protocol.preparer

	cp['device_description'] = protocol.device_description 
	cp['intended_use'] = protocol.intended_use
	cp['indication_of_use'] = protocol.indication_of_use
	cp['comparator_devices'] = protocol.comparator_devices.split(",") if protocol.comparator_devices else []
	cp['sota_description'] = protocol.sota_description 
	cp['sota_product_name'] = protocol.sota_product_name 

	cp['scope'] = protocol.scope 
	cp['years_back'] = protocol.years_back

	if protocol.lit_date_of_search:
		cp['lit_date_of_search'] = protocol.lit_date_of_search.strftime('%b %d, %Y')
		if protocol.lit_start_date_of_search:
			cp['start_lit_date_of_search'] = protocol.lit_start_date_of_search.strftime('%b %d, %Y')
		else:
			cp['start_lit_date_of_search'] =  (protocol.lit_date_of_search - relativedelta(years=protocol.years_back)).strftime('%b %d, %Y')

	else:
		cp['lit_date_of_search'] = ""
		cp['start_lit_date_of_search'] = ""

	if protocol.ae_date_of_search:
		cp['ae_date_of_search'] = protocol.ae_date_of_search.strftime('%b %d, %Y')
		if protocol.ae_start_date_of_search:
			cp['ae_start_date_of_search'] = protocol.ae_start_date_of_search.strftime('%b %d, %Y')
		else:
			cp['ae_start_date_of_search'] =  (protocol.ae_date_of_search - relativedelta(years=protocol.ae_years_back)).strftime('%b %d, %Y')
	else:
		cp['ae_date_of_search'] = ""

	if protocol.safety_claims:
		cp['safety_claims'] = protocol.safety_claims
	else:
		cp['safety_claims'] = ""
	
	if protocol.performance_claims:
		cp['performance_claims'] = protocol.performance_claims
	else:
		cp['performance_claims'] = ""

	if protocol.other_info:
		cp['other_info'] = protocol.other_info
	else:
		cp['other_info'] = ""


	cp['lit_search_databases'] = get_database_list(protocol, False)
	cp['ae_databases'] = get_database_list(protocol, True)

	exclusion_reasons = []
	exclusion_reasons_list = ExclusionReason.objects.filter(literature_review = lit_review)

	for exclusion_reason in exclusion_reasons_list:
		exclusion_reasons.append(exclusion_reason.reason)
	cp['exclusion_reasons'] = exclusion_reasons	

	# Extraction Fields 
	extractions = ExtractionField.objects.filter(literature_review=lit_review, field_section="EF").order_by("field_order")
	extractions_list = []
	for extraction in extractions:
		extractions_list.append({
			"name": extraction.name.replace("_", " ").title(),
			"category": extraction.category,
		})
	cp['extraction_fields'] = extractions_list	

	#print("CP Build: \n {0}".format(cp))

	return cp 


def get_protocol_path(review_id):

	pass 