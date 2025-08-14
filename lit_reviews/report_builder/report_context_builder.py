



from lit_reviews.report_builder.appendices import *
from lit_reviews.report_builder.prisma import prisma
from backend.logger import logger

### we probably can just do these all in tasks.py method if they're just single function calls...


def prisma_context(lit_review_id):

	prisma_context = prisma(lit_review_id)
	return prisma_context

def appendix_a1_context(lit_review_id):

	pass
	## get protocol info
	## get Sota tables 
	sota_context = appendix_a(lit_review_id=lit_review_id, sota=True)
	print("sota context retrieved" + str(sota_context))
	return sota_context

	
def appendix_a2_context(lit_review_id):

	device_context = appendix_a(lit_review_id=lit_review_id, sota=False)

	print("device context buildt {0}".format(device_context))

	return device_context


def appendix_b_context(lit_review_id, retained_and_included):

	
	context = appendix_b(lit_review_id, retained_and_included)

	return context


def appendix_c_context(lit_review_id):

	context = {"sota_table": {},
			   "suitability_retinc_table": {},
			   "suitability_all_table": {},
			   "data_contribution_retinc_table": {},
			   "extraction_summary_table": {},
			   "extraction_detail_table": {},
			   "excluded_table": {},
			  }

	index_tables = 0
	context['sota_table']['rows'] = appendix_c(lit_review_id, 'sota')
	if len(context['sota_table']['rows']) > 0:
		index_tables = index_tables + 1
		context['sota_table']['table_index'] = index_tables
	else:
		context['sota_table']['table_index'] = index_tables
		
	context['suitability_retinc_table']['rows'] = appendix_c(lit_review_id, 'suitability_retinc')
	if len(context['suitability_retinc_table']['rows']) > 0:
		index_tables = index_tables + 1
		context['suitability_retinc_table']['table_index'] = index_tables
	else:
		context['suitability_retinc_table']['table_index'] = index_tables

	context['suitability_all_table']['rows'] = appendix_c(lit_review_id, 'suitability_all')
	if len(context['suitability_all_table']['rows']) > 0:
		index_tables = index_tables + 1
		context['suitability_all_table']['table_index'] = index_tables
	else:
		context['suitability_all_table']['table_index'] = index_tables

	# index_tables = index_tables + 1
	# context['appraisal_of_clinical_lit_data_cont_table_index'] = index_tables

	context['data_contribution_retinc_table']['rows'] = appendix_c(lit_review_id, 'datacontribution_retinc')
	if len(context['data_contribution_retinc_table']['rows']) > 0:
		index_tables = index_tables + 1
		context['data_contribution_retinc_table']['table_index'] = index_tables
	else:
		context['data_contribution_retinc_table']['table_index'] = index_tables

	# This section Been Commented because it not used now in the Report Document
	# context['extraction_summary_table']['rows'] = appendix_c(lit_review_id, 'extraction_summary')
	# if len(context['extraction_summary_table']['rows']) > 0:
	# 	index_tables = index_tables + 1
	# 	context['extraction_summary_table']['table_index'] = index_tables
	# else:
	# 	context['extraction_summary_table']['table_index'] = index_tables

	context['extraction_detail_table']['rows'] = appendix_c(lit_review_id, 'extraction_detail')
	if len(context['extraction_detail_table']['rows']) > 0:
		index_tables = index_tables + 1
		context['extraction_detail_table']['table_index'] = index_tables
	else:
		context['extraction_detail_table']['table_index'] = index_tables

	context['excluded_table']['rows']= appendix_c(lit_review_id, 'excluded')
	if len(context['excluded_table']['rows']) > 0:
		index_tables = index_tables + 1
		context['excluded_table']['table_index'] = index_tables
	else:
		context['excluded_table']['table_index'] = index_tables

	logger.debug("context {0}".format(context))
	return context 


def appendix_d_context(lit_review_id):
	
	context = {"all_retained_table": {} }
	context['all_retained_table']['rows'] = appendix_d(lit_review_id)
	return context


def appendix_e_context(lit_review_id, date_of_search, date_end):

	context = {}

	context['maude_tables'] = appendix_e_maude(lit_review_id, date_of_search, date_end)
	
	context['ae_dbs'] = appendix_e_aes(lit_review_id, is_vigilance=False, date_of_search=date_of_search, date_end=date_end)
	context['recall_dbs'] = appendix_e_recalls(lit_review_id, is_vigilance=False, date_of_search=date_of_search, date_end=date_end)

	## faers_tables missing... needed?
	# None for now we'll be added it if needed.
	context['faers_tables'] = None

#	context = appendix_e(lit_review_id=1, is_vigilance=False, date_of_search=None, date_end=None):
	return context
	## need to read the report and add contexts here 
	## definitely by database top level,  then multiple tables per DB
	## separate beginning section for maude. 



