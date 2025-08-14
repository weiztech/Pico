

boilerplate_protocol = {
	
	"overview": {
	
		"background": "The literature search will identify data not held by the manufacturer that are needed for the clinical evaluation. The literature search will identify potential sources of clinical data for establishing:",
		"background_bullets": [
			"Clinical data relevant to the devices under evaluation and to the equivalent devices for which equivalency has been demonstrated",
			"Current knowledge/ the state of the art."

		], 

		"equiv_reqs": "In line with MEDDEV 2.7/1 rev 4, Clinical, technical and biological characteristics will be taken into consideration for the demonstration of equivalence. \
		Information obtained on these devices have established equivalence to the [DEVICENAME] based on the criteria below (Table 4).  ",

		"equiv_reqs_bullets":[
		"Clinical characteristics including clinical purpose, same intended purposes, same patient population and not foreseen to deliver significantly clinically different device performance.",
		"Technological characteristics including principle of action, conditions of use, and locations of use.",
		"Biological characteristics. ",
		"The equivalent devices are CE certified.",

		]
	


	},
	"criteria" :{


		"scope":"The scope of the literature search includes a query of select adverse event report databases, as well as scientific databases, for the past [SEARCHTERM] years. This period of time is felt to provide sufficient clinical experience with these devices from both a safety and performance perspective",
		"person": "Edward Drower, M.S.",
		"period_covered": "[SEARCHTERM] years prior to Date of Search, unless otherwise stated. Literature sources used to identify data.",
		"sci_dbs": [
				"PubMed® comprises more than 30 million citations for biomedical literature from MEDLINE, life science journals, and online books. Citations may include links to full-text content from PubMed Central and publisher web sites.  It backs to 1966.PubMed Central",
				"PubMed Central® (PMC) is a full-text archive of biomedical and life sciences journal literature at the U.S. National Institutes of Health's National Library of Medicine (NIH/NLM).",
				"Cochrane Library - The Cochrane Library is a collection of databases that contain different types of high quality, independent evidence in health care provided by Cochrane groups. As its core is the Cochrane Database Systematic Reviews (CDSR), a database of peer-reviewed systematic reviews in health care prepared by Cochrane Review Groups",
				"ClinicalTrials.gov is a registry of clinical trials. It is run by the United States National Library of Medicine (NLM) at the National Institutes of Health, and is the largest clinical trials database, holding registrations from over 329,000 trials from 209 countries. This database encompasses globally run trials",
		],
		"ae_dbs": [
			"US FDA MAUDE Database (USA)",
			"US FDA Recalls Database (USA)",
			"Publicly accessible medical device safety information organized by product device codes granted with FDA Clearance.",
			"UK MHRA - Publicly accessible medical device safety information including safety alerts, recalls and adverse events.",
		],
		"search_details": "Because different databases offer differing limiting options and search fields, different approaches will be taken as appropriate to the database.  All unique circumstances will be identified in the final report.  All searches will be performed through online databases.",
		"dupes1": "Duplicate citations found in the search results of the databases will be screened and removed prior to any review. The duplicate counts shall be captured in the final review and summarized in search-term tables.",
		"dupes2": "A duplicate citation is identified through electronic signatures based on a match in one of the following fields of information across the databases.",
		"dupes3_bullets": [
			"PubMed Unique Identifier",
			"PubMed Central Unique Identifier",
			"Cochrane Library Unique Identifier",
			"Academic Citation (in APA format)",
		]
	},
	"focused_search" : {

		"fs1": "The resulting number of citations (abstracts) from each database search outlined (less duplicates) is captured and reviewed electronically.  ",
		"fs2": "Search term relevancy criteria is established to promote the most efficient review of appropriate citations for the devices.  Searches terms results with citation results in excess of 200 are considered too broad and are excluded from the review process.  In contrast, search terms without citation results (i.e. zero) are considered too narrow.  All search term citation results are tabulated in the final result tables. ",
		"fs3": "The search results (abstracts identified) are reviewed in detail and assessed for relevancy to similar, equivalent or exact systems for clinical safety and efficacy.  Similar based studies (i.e. no unique safety or efficacy results) are considered duplicate information and only referenced once. The analysis of each study reviewed is conducted based on the criteria below. ",

		"select_criteria": "The following criteria is used to assess the suitability of material (articles, reports, etc.) for inclusion/exclusion in the analysis stage of this report.",

		"inclusion_bullets": [

			"Citation addresses performance, risks, and/or safety of the ArcScan Insight 100  (products or equivalent products).",
			"Products are used in ways like indications for use of the ArcScan Insight 100 products.",
			"Any articles considered relevant to the state of the art/current knowledge identified during this search will be included in the state-of-the-art section",
		],
		"exclusion_bullets": [

			"Citation describes technical or non-clinical study results only.",
			"Study design contains unsubstantiated opinions.",
			"Study design contains insufficient information to undertake a scientific analysis.",
			"Full text of the citation cannot be interpreted due to limitations in obtaining appropriate translations.",
			"Abstract or full paper could not be retrieved.",
			"Papers including multiple devices and/or combined treatment with medicinal products from which it is not possible to extract safety or performance data for the target devices/equivalent devices.",

		],
		"exclusion": "Clinical literature shall also be excluded in situations where multiple papers appear to report on the same study. Consideration shall be given to the extent of duplication and reported safety or performance outcomes, prior to the excluding of any literature.",
	

	},
	"outputs": {

		"intro": "All literature citations selected for inclusion is listed as References.",
		"process": "Figure 1 visually outlines the process used in assessing citations retrieved from queries of online databases for suitability for inclusion in the clinical evaluation report",


	},

	"scientific_databases": {
		"strategy_p": "The following limits were applied to the search:",
		"dbs": [
			{
			   "name": "PubMed",
			   "link": "https://www.ncbi.nlm.nih.gov/pubmed",
			   "strat_bullets": [
			   		"Publication dates: [SEARCHTERM] years prior to Date of Search",
			   		"Species: Humans",
			   		"Languages: English",
			   ]

			},
			{
			"name": 'PubMed Central',
			"link": "https://www.ncbi.nlm.nih.gov/pmc",
			"strat_bullets": [
			   		"Publication dates: [SEARCHTERM] years prior to Date of Search",
			   		"Species: Humans",
			   		"Languages: English",
			   ]
			},
			{
				"name": "Cochrane Library",
				"link": "http://www.cochranelibrary.com/",
				"strat_bullets": [ 
					"Search: Title, Abstracts, Keywords",
					"Article types: Clinical Trial, Controlled Clinical Trial, Meta-analysis, Randomized controlled trial where data has been published ",
					"Publication dates: [SEARCHTERM] years prior to Date of Search",
					"Species: Humans",
					"Languages: English"
				]

			},

			{
				"name": 'ClinicalTrials.gov',
				"link": "http://www.clinicaltrials.gov/ ",
				"link": "http://www.cochranelibrary.com/",
				"strat_bullets": [ 
					"Search: Title, Abstracts, Keywords",
					"Article types: Clinical Trial, Controlled Clinical Trial, Meta-analysis, Randomized controlled trial where data has been published ",
					"Publication dates: [SEARCHTERM] years prior to Date of Search",
					"Species: Humans",
					"Languages: English"
					]
			}
		]	
			 
	},

	"appr_plan": {
		"intro": "The following section outlines the criteria for suitability and data contribution used to appraise the literature to be included in this clinical evaluation (adapted from MEDDEV 2.7/1, Rev.4). ",

	},
	"analysis_plan": {
		"intro": "Citations selected for in-depth review are qualitatively summarized to include:",
		"bullets1": [
			"An overall study evaluation",
			"A transformation table of evaluation criteria included in Tables 2 and 3.",
			"An in-depth analysis of the citation",
		],
		"bullets2": [
			"Reported Safety Data",
			"New identified Risks",
			"Performance Benefits/Issues",
		]
	},

	"ae_maude": {
		
			'strategy_p1':"The safety database and recall search will be based on the 510K code ([REPLACECODE])",
			'strategy_p2': "If the number of safety events reported exceeded the download limits of 500, the first 500 most current events will be captured under the coding and were reviewed to assess relevance to the current medical devices.",

		

	},

	"ae_maude_recalls": {


	},

	"ae_mhra": {


	}
			
}

	
			

