## schema of protocll



search_protocol = {
	
	"search_protocol": {

		"version_number":"", ## incremented val passed from FinallReportJob() object.
		"company_logo": "", ## Image,  Client.logo 
		"device_name": "",  ## LiteratureReview.device.name
		"device_classification": "", ## LiteratureReview.device.classification
		"company_name": "", ## LiteratureReview.client.name
		"company_address": "", ## LiteratureReview.client.full_address_string
		"prepared_date": "", ## Date.today() 

		"device_description": "", # SearchProtocol.device_description
		"intended_use": "", #SearchProtocol.intended_use
		"comparator_devices": "", #SearchProtocol.comparator_devices
		"sota_description": "", #SearchProtocol.sota_description
		"sota_product_name": "", #SearchProtocol.sota_product_name

		"years_back": "", #SearchProtocol.years_back
		"ae_years_back": "",  #SearchProtocol.ae_years_back

		"lit_date_of_search": "", #SearchProtocol.lit_date_of_search
		"ae_date_of_search":"", #SearchProtocol.ae_date_of_search
		"exclusion_reasons":[], #ExclusionReason(literature_review = this lit_review)

		"lit_search_databases": [
			{ 
				"name": "",#SearchProtocol.lit_searches_databases_to_search.name
				"url": "", #SearchProtocol.lit_searches_databases_to_search.url
				"description": "", ## Nonexistant TODO**
				"terms": ["", "term2", "term3"] , ## LiteratureSearch(db__name=this name).term
				"search_strategy": ["item 1", "item 2"], ## Nonexistant TODO**
			},
			{
				"name": "",#SearchProtocol.lit_searches_databases_to_search.name
				"description": "",
				"terms": ["", "term2", "term3"] , ## LiteratureSearch(db__name=this name).term
				"search_strategy": ["" ] ## Nonexistant TODO**

			},
			

		]

	},

	"ae_databases": [
{ 
				"name": "",#SearchProtocol.ae_databases_to_search.name
				"url": "", #SearchProtocol.ae_searches_databases_to_search.url

				"description": "", #SearchProtocol.ae_databases_to_search.description
				"terms": ["", "term2", "term3"] , ## LiteratureSearch(db__name=this name).term

			},
			{
				"name": "",#SearchProtocol.ae_databases_to_search.name
				"url": "", #SearchProtocol.ae_searches_databases_to_search.url
				"description": "",#SearchProtocol.ae_databases_to_search.description
				"terms": ["", "term2", "term3"] , ## LiteratureSearch(db__name=this name).term
				"search_strategy": ["" ] ## Nonexistant TODO**

			},
			
	]

}


## todos udpate descirption of each NCBIDatabase

## report schema 

review = {

	"prisma":{

	"all_reviews": "",
	"sota_extra_reviews":"",
	"reviews_no_dupes": "",
	"total_screened": "",
	"reviews_excluded": "",
	"reviews_retained":"",


	"exclusion_reason_counts":{

		"custom": "",
		"ft-excluded": "",
		"retinc": "",

		"rows": [

			{
				"Reason": "",
				"Count": "",
			}

		]

	}

	}
	
	"appendix_a1" : [

				{
					"table_index": "", # table index will be increased every time there is  a database that has more than 0 terms	
					"protocol": {} ## protocol obj from same func that generated the search_protocol

					"results_summary_table":{

					"headers": ["Search Term", "Publications Yielded","Duplicate Results", "Included", "Excluded"],

					"rows": [
							{
								"Search Term": "",
								"Publications Yielded": "",
								"Duplicate Results": "",
								"Included": "",
								"Excluded": "",
							 },

						## etc. 
						]
					}

				}
	],


	"appendix_a2" : [

				{
					"table_index": "", # table index will be increased every time there is  a database that has more than 0 terms	
					
					"protocol": {} ## protocol obj from same func that generated the search_protocol

					"results_summary_table":{

					"headers": ["Search Term", "Publications Yielded","Duplicate Results", "Included", "Excluded"],

					"rows": [
							{
								"Search Term": "",
								"Publications Yielded": "",
								"Duplicate Results": "",
								"Included": "",
								"Excluded": "",
							 },

						## etc. 
						]
					}
				}
	],
	

	"appendix_b_retinc": [


		{
					"table_index": "", # table index will be increased every time there is  a database that has more than 0 terms	

					"protocol": {} ## protocol obj from same func that generated the search_protocol

					"results_table":{

					#"headers": ["Search Term", "Publications Yielded","Duplicate Results", "Included", "Excluded"],

					"rows": [
							{
								"Term": "",
								"Citation": "",
			''					"S": "",
								"I": "",
								"Justification": "",
							 },

						## etc. 
						]
					}
				}
	],
	"appendix_b_all": [

	{
		"table_index": "", # table index will be increased every time there is  a database that has more than 0 terms	
		
		"protocol": {} ## protocol obj from same func that generated the search_protocol

		"results_table":{

		"headers": ["Search Term", "Publications Yielded","Duplicate Results", "Included", "Excluded"],

		"rows": [
				{
					"Term": "",
					"Citation": "",
					"S": "",
					"I": "",
					"Justification": "",
				 },

			## etc. 
			]
		}
	},

	"appendix_a1_table_count": "", # total number of appendix_a1 tables (if db has no terms there will be no table for it)
	"appendix_a2_table_count": "", # total number of appendix_a2 tables (if db has no terms there will be no table for it)
	"appendix_b_retinc_table_count": "", # total number of appendix_b_retinc tables (if db has no terms there will be no table for it)
	"appendix_b_all_table_count": "", # total number of appendix_b_all tables (if db has no terms there will be no table for it)
	"dynamique_tables_count": "", # total number of tables for all appendices

	"appendix_c":{


		"sota_table": {

			"rows": [ 

				{
					"id": "",
					"Citation":"",
					"SoTA Classification":"",
					"Exclusion Reason":"",



				}
			],

		},

		"suitability_retinc_table": {

			"rows": {

				"id": "",
				"Citation":""
				"Device":"",
				"Application":"",
				"Population": "",
				"Report":"",

			},
		},


		"suitability_all_table": {

		"rows": None,
		},


		"data_contribution_retinc_table":{


			"rows": {
				"Citation":"",
				"Design":"",
				"Outcomes": "",
				"Followup": "",
				"Stats": "",
				"Study Size":"",
				"Clinical Significance":"",
				"Clear Conc":"",
			},

		},

		"extraction_summary_table:"{


			"rows":{
				"id": "",
			"Safety": "",
			"Performance":"",
			"Adverse Events":"",
			"SoTA":"",
			"Guidance":"",
			"Other": "",
			"Study Design":"",
			"Total Sample Size": "",
			"Objective": "",
			"Treatment Modality":"",
			"Study Conclusions": "",
			"GRADE Numerical Score": "",
		


			},

		}

		"extraction_detail_table":{

		"rows": {

			"id": "",
			"Citation":"",
			"Safety": "",
			"Performance":"",
			"Adverse Events":"",
			#"SoTA":"",
			"Guidance":"",
			"Other": "",
			"Study Design":"",
			"Total Sample Size": "",
			"Objective": "",
			"Treatment Modality":"",
			"Study Conclusions": "",
			"GRADE Study Design": "",
			"GRADE Numerical Score": "",
			"Additional Comments": "",

		},

		"excluded_table": {

			"rows":None,

		},

	}


	},

	"appendix_d": {

		"all_retained_table": {


			"rows": {

				"Citation": "",
			}


		},


	},

	"appendix_e":{

	"maude_tables": {

		"maude_aes": {
	
			"protocol": {


				"name": "",#SearchProtocol.lit_searches_databases_to_search.name
				"url": "", #SearchProtocol.lit_searches_databases_to_search.url
				"description": "", ## Nonexistant TODO**
				"terms": ["", "term2", "term3"] , ## LiteratureSearch(db__name=this name).term
				"search_strategy": ["item 1", "item 2"], ## Nonexistant TODO**

			}	


		##  summary of all events (full date range)
		"single_row_summary":{

			{
		        "Date of Search": date_of_search,
		        "Date End": date_end,
		        "Database": db,
		        "Death": death,
		        "Injury": injury,
		        "Malfunction": malfunction,
		        "Other/NA": na_other,
		        "Excluded": excluded,
    		}

		}

		## summary of maude events by year 
		"maude_by_year":	{

				"rows": [

					"Year": "",
					"Deaths":"",
					"Injuries": "",
					"Malfunctions": "",
					"Other/NA": "",


				]

			}
		
		"maude_included_events":{

			"rows": [
				{
					"Manufacturer": "",
					"Term": "",
					"Event Type": "",
					"Description": "",
				}

			],


## all maude AEs for rendering the appendix E2

		"E2_maude_aes": {

			"rows": [

				"Manufacturer": "",
				"Term": "",
				"Event Type": "",
				"Description":"", 

			]


		}

		}
		},

		"maude_recalls": {


		
			"by_year": {

				"rows": [

		            "Year",
		            "Recall Class 1",
		            "Recall Class 2",
		            "Recall Class 3",
				]
			## some kind of recall table summary
			},

			"included": {

				"rows": [
					"Term": "",
					"Event Date": "",
					"Recall Class": "",
					"Recall Reason": "",

				]



			}

		}

	},
	"faers_tables":{} ## not sure if we need this. 
	"ae_dbs":[
	 	{

	 	"protocol": {

				"name": "",#SearchProtocol.lit_searches_databases_to_search.name
				"url": "", #SearchProtocol.lit_searches_databases_to_search.url
				"description": "", ## Nonexistant TODO**
				"terms": ["", "term2", "term3"] , ## LiteratureSearch(db__name=this name).term
				"search_strategy": ["item 1", "item 2"], ## Nonexistant TODO**

	 	},
	 	# protocol_context_builder.get_db_info(literature_review, db)
		# serch strategy
		# search terms

		# included results (all results for db), term, number, description
		"included": {
			"rows":[

			"Term": "",
			"Number": "",
			"Description": "",


			],


		}
		"summary": "",
		},

	],
	"recall_dbs": [
	 	{

	 	"protocol": {

				"name": "",#SearchProtocol.lit_searches_databases_to_search.name
				"url": "", #SearchProtocol.lit_searches_databases_to_search.url
				"description": "", ## Nonexistant TODO**
				"terms": ["", "term2", "term3"] , ## LiteratureSearch(db__name=this name).term
				"search_strategy": ["item 1", "item 2"], ## Nonexistant TODO**
	 	
	 	},
	 	# protocol_context_builder.get_db_info(literature_review, db)
		# serch strategy
		# search terms

		# included results (all results for db), term, number, description
		"included": {
			"rows":[

			"Term": "",
			"Number": "",
			"Description": "",


			],


		},
     	"summary": "",

		},

	],






	}




}

