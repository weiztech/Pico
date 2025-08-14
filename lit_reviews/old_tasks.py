"""
This file include past auto search functions for each database.
in case we need to go back and use it for a specefic db in the future 
it'll be easy to switch over.
"""

# @shared_task
# def pubmed_scraper(search_term, url_filter, lit_review_id=None, lit_search_id=None):
#     try:
#         search_protocol = SearchProtocol.objects.get(literature_review__id=lit_review_id)
#         max_imported_search_results = search_protocol.max_imported_search_results

#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         if lit_search:
#             disable_exclusion = lit_search.disable_exclusion
#         else:
#             disable_exclusion = False

#         pubmed_obj = pubmed.Pubmed(search_term, url_filter, lit_review_id)
#         result_file_source = pubmed_obj.get_result(max_imported_search_results, disable_exclusion)

#         if result_file_source == "Results out of range":
#             result_count = int(str(pubmed_obj.result_count).replace(",", ""))
#             lit_search.search_file_url = None
#             lit_search.search_file = None
#             lit_search.save()
#             run_single_search(lit_search_id, result_count)
#             return "Results out of range"

#         file_name, FILE_PATH = create_file_path(search_term, lit_search.db.name)
#         with open(FILE_PATH, 'wb') as f:
#             f.write(result_file_source)

#         # upload file aws s3
#         upload_to = "uploads/" + file_name
#         file_url = upload_file_to_aws_s3(FILE_PATH, upload_to)
#         lit_search.search_file_url = file_url
#         lit_search.save()
#         logger.debug("lit url: {0}".format(lit_search.search_file_url))
#         run_single_search(lit_search_id)

#         return "success"

#     except Exception as e:
#         error_msg = str(traceback.format_exc())
#         logger.error("error inside pubmed auto search scraper: {0}".format(error_msg))
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         import_status = "INCOMPLETE-ERROR"
#         lit_search.import_status = import_status
#         lit_search.error_msg = str(e) + " ," + "Please contact support for a solution"
#         lit_search.save()
#         return "error"
        
# @shared_task
# def cochrane_scraper(search_term, lit_review_id=None, lit_search_id=None):
#     try:
#         search_protocol = SearchProtocol.objects.get(literature_review__id=lit_review_id)
#         max_imported_search_results = search_protocol.max_imported_search_results
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         if lit_search:
#             disable_exclusion = lit_search.disable_exclusion
#         else:
#             disable_exclusion = False
#         start_date, end_date = get_search_params(lit_search)

#         file_name, FILE_PATH = create_file_path(search_term, lit_search.db.name, ".txt")
#         cochrane_obj = cochranelibrary.CochraneLibrary(settings.TMP_ROOT, start_date, end_date)
#         result_file_name, result_count = cochrane_obj.search(search_term, max_imported_search_results ,disable_exclusion)
#         if result_file_name == "Results out of range":
#             lit_search.search_file_url = None
#             lit_search.search_file = None
#             lit_search.save()
#             run_single_search(lit_search_id, result_count)
#             return "Results out of range"

#         result_file_path = os.path.join(settings.TMP_ROOT, result_file_name)
#         # upload file aws s3
#         upload_to = "uploads/" + file_name
#         file_url = upload_file_to_aws_s3(result_file_path, upload_to)
#         lit_search.search_file_url = file_url
#         lit_search.save()
#         logger.debug("lit url: {0}".format(lit_search.search_file_url))
#         run_single_search(lit_search_id)

#         return "success"

#     except Exception as e:
#         logger.error("Error Occured: {0}".format(str(e)))
#         logger.error("Traceback: {0}".format(traceback.format_exc()))

#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         import_status = "INCOMPLETE-ERROR"
#         lit_search.import_status = import_status
#         lit_search.error_msg = str(e) + " ," + "Please contact support for a solution"
#         lit_search.save()
#         return "error"


# @shared_task
# def pubmed_central_scraper(search_term, lit_review_id=None, lit_search_id=None):
#     try:
#         search_protocol = SearchProtocol.objects.get(literature_review__id=lit_review_id)
#         max_imported_search_results = search_protocol.max_imported_search_results
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         if lit_search:
#             disable_exclusion = lit_search.disable_exclusion
#         else:
#             disable_exclusion = False

#         file_name, FILE_PATH = create_file_path(search_term, lit_search.db.name, ".csv")
#         start_date, end_date = get_search_params(lit_search)
#         obj = pubmed_central.PubmedCentral(settings.TMP_ROOT)
#         result_count, new_file_name =  obj.search(search_term, start_date, end_date, max_imported_search_results, disable_exclusion)
        
#         # Closing the webdriver
#         obj.driver.quit()
#         if result_count >= 1:
#             if new_file_name == "Results out of range":
#                 lit_search.search_file_url = None
#                 lit_search.search_file = None
#                 lit_search.save()
#                 run_single_search(lit_search_id, result_count)
#                 return "Results out of range"
#             else:
#                 result_file_source = os.path.join(settings.TMP_ROOT, new_file_name)
#                 # upload file aws s3
#                 upload_to = "uploads/" + file_name
#                 file_url = upload_file_to_aws_s3(result_file_source, upload_to)
#                 lit_search.search_file_url = file_url
#                 lit_search.save()
#                 logger.debug("lit url: {0}".format(lit_search.search_file_url))
#                 run_single_search(lit_search_id)
#                 return "success"

#         else:
#             import_status = "INCOMPLETE-ERROR"
#             lit_search.import_status = import_status
#             lit_search.error_msg = "Results out of range for this term ,Please contact support for a solution" 
#             lit_search.save()
#             return "Results out of range. Result number : {}".format(result_count)

#     except Exception as e:
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         error_track = str(traceback.format_exc())
#         logger.error(error_track)
#         import_status = "INCOMPLETE-ERROR"
#         lit_search.import_status = import_status
#         lit_search.error_msg = str(e) + " ," + "Please contact support for a solution"
#         lit_search.save()
#         return "error"


# @shared_task
# def clinical_trials_scraper(search_term, url_filter, lit_review_id=None, lit_search_id=None):
#     try:
#         # get search info
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         search_protocol = SearchProtocol.objects.get(literature_review__id=lit_review_id)
#         max_imported_search_results = search_protocol.max_imported_search_results
#         if lit_search:
#             disable_exclusion = lit_search.disable_exclusion
#         else:
#             disable_exclusion = False

#         file_name, FILE_PATH = create_file_path(search_term, lit_search.db.name, ".csv")
#         obj = clinical_trials.ClinicalTrials(search_term, url_filter)
#         result_number, content = obj.search(max_imported_search_results ,disable_exclusion)

#         if content != "Results out of range":
#             with open(FILE_PATH, 'wb') as f:
#                 f.write(content)


#             # upload file aws s3
#             upload_to = "uploads/" + file_name
#             file_url = upload_file_to_aws_s3(FILE_PATH, upload_to)
#             lit_search.search_file_url = file_url
#             lit_search.save()
#             logger.debug("lit url: {0}".format(lit_search.search_file_url))
#             run_single_search(lit_search_id)

#             return "success"
    
#         else:
#             lit_search.search_file_url = None
#             lit_search.search_file = None
#             lit_search.save()
#             run_single_search(lit_search_id, result_number)
#             return "Results out of range. Result number : {}".format(result_number)
            
#     except Exception as e:
#         error_track = str(traceback.format_exc())
#         logger.error(error_track)
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         import_status = "INCOMPLETE-ERROR"
#         lit_search.import_status = import_status
#         lit_search.error_msg = str(e) + " ," + "Please contact support for a solution"
#         lit_search.save()
#         return "error"

# @shared_task
# def maude_fda_scraper(search_term,start_date, end_date, lit_review_id=None, lit_search_id=None):
#     try:
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         )
#         file_name, FILE_PATH = create_file_path(search_term, lit_search.db.name, ".csv")
        
#         maude_obj = maude_scraper.MaudeFda(settings.TMP_ROOT)
#         new_file_name = maude_obj.search_and_get_result(search_term, start_date, end_date)

#         if new_file_name == "No results found.":
#             import_status = "INCOMPLETE-ERROR"
#             lit_search.import_status = import_status
#             lit_search.error_msg = "No results found for this term ,Please contact support for a solution" 
#             lit_search.save()
#             return "No results found."
            
#         else:
#             logger.debug("new file name: {0}".format(new_file_name))
#             result_file_source = os.path.join(settings.TMP_ROOT, new_file_name)

#             # upload file aws s3
#             upload_to = "uploads/" + file_name
#             file_url = upload_file_to_aws_s3(result_file_source, upload_to)
#             lit_search.search_file_url = file_url
#             lit_search.save()
#             logger.debug("lit url: {0}".format(lit_search.search_file_url))
#             run_single_search(lit_search_id)
#             return "success"

#     except Exception as e:
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         import_status = "INCOMPLETE-ERROR"
#         lit_search.import_status = import_status
#         lit_search.error_msg = str(e) + " ," + "Please contact support for a solution"
#         lit_search.save()
#         return "error"


# @shared_task
# def europe_pmc_scraper(search_term,start_date, end_date, lit_review_id=None, lit_search_id=None):
#     try:
#         search_protocol = SearchProtocol.objects.get(literature_review__id=lit_review_id)
#         max_imported_search_results = search_protocol.max_imported_search_results
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         )
#         if lit_search:
#             disable_exclusion = lit_search.disable_exclusion
#         else:
#             disable_exclusion = False
#         start_date_obj = datetime.datetime.strptime(str(start_date),'%m/%d/%Y')
#         end_date_obj = datetime.datetime.strptime(str(end_date),'%m/%d/%Y')

#         file_name, FILE_PATH = create_file_path(search_term, lit_search.db.name, ".ris")
#         europe_pmc_obj = europe_pmc.EuropePMC(settings.TMP_ROOT)
#         new_file_name, message, result_count = europe_pmc_obj.search(search_term, start_date_obj, end_date_obj, max_imported_search_results, disable_exclusion)


#         if message != "successfully downloaded.":
#             if message == "Results out of range":
#                 lit_search.search_file_url = None
#                 lit_search.search_file = None
#                 lit_search.save()
#                 run_single_search(lit_search_id, result_count)
#                 return "success"
            
#         else:
#             logger.debug("new file name: {0}".format(new_file_name))
#             result_file_source = os.path.join(settings.TMP_ROOT, new_file_name)

#             # upload file aws s3
#             upload_to = "uploads/" + file_name
#             file_url = upload_file_to_aws_s3(result_file_source, upload_to)
#             lit_search.search_file_url = file_url
#             lit_search.save()
#             logger.debug("lit url: {0}".format(lit_search.search_file_url))
#             logger.debug("lit_search.db.entrez_enum: {0}".format(lit_search.db.entrez_enum))
#             run_single_search(lit_search_id)
#             return "success"

#     except Exception as e:
#         lit_search = LiteratureSearch.objects.get(
#             id=lit_search_id
#         ) 
#         import_status = "INCOMPLETE-ERROR"
#         lit_search.import_status = import_status
#         lit_search.error_msg = str(e) + " ," + "Please contact support for a solution"
#         lit_search.save()
#         return "error"