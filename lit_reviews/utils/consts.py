# url filter: age
pubmed_age = {
    "80 and over: 80+ years": "80andover",
    "Adolescent: 13-18 years": "adolescent",
    "Adult: 19-44 years": "adult",
    "Infant: 1-23 months": "infant",
    "Aged: 65+ years": "aged",
    "Adult: 19+ years": "alladult",
    "Child: birth-18 years": "allchild",
    "Infant: birth-23 months": "allinfant",
    "Child: 6-12 years": "child",
    "Middle Aged: 45-64 years": "middleaged",
    "Middle Aged + Aged: 45+ years": "middleagedaged",
    "Newborn: birth-1 month": "newborn",
    "Preschool Child: 2-5 years": "preschoolchild",
    "Young Adult: 19-24 years": "youngadult",
}

# url filter: pubt
pubmed_article_types = {
    "Books and Documents": "booksdocs",
    "Clinical Trial": "clinicaltrial",
    "Randomized Controlled Trial": "randomizedcontrolledtrial",
    "Review": "review",
    "Systematic Review": "systematicreview",
    "Meta-Analysis": "meta-analysis",
}

# url filter: age
clinical_trials_age_group = {
    "Child (birth-17)": "0",
    "Adult (18-64)": "1",
    "Older Adult (65+)": "2",
}

# api filter: StdAge
clinical_trials_api_age_group = {
    "Child (birth-17)": "CHILD",
    "Adult (18-64)": "ADULT",
    "Older Adult (65+)": "OLDER_ADULT",
}

# url filter: recrs
clinical_trials_recruitment_status = {
    "Not yet recruiting": "b",
    "Recruiting": "a",
    "Enrolling by invitation": "f",
    "Active not recruiting": "d",
    "Suspended": "g",
    "Terminated": "h",
    "Completed": "e",
    "Withdrawn": "i",
    "Unknown status": "m",
}

# url filter for OverallStatus => combines both (Recruitment Status - Expanded Access Status) 
clinical_trials_api_overall_status = {
    "Not yet recruiting": "NOT_YET_RECRUITING",
    "Recruiting": "RECRUITING",
    "Enrolling by invitation": "ENROLLING_BY_INVITATION",
    "Active not recruiting": "ACTIVE_NOT_RECRUITING",
    "Suspended": "SUSPENDED",
    "Terminated": "TERMINATED",
    "Completed": "COMPLETED",
    "Withdrawn": "WITHDRAWN",
    "Unknown status": "UNKNOWN",
    "Available": "AVAILABLE",
    "No longer available": "NO_LONGER_AVAILABLE",
    "Temporarily not available": "TEMPORARILY_NOT_AVAILABLE",
    "Approved for marketing": "APPROVED_FOR_MARKETING",
}

# url filter: recrs
clinical_trials_expanded_access_status = {
    "Available": "c",
    "No longer available": "j",
    "Temporarily not available": "k",
    "Approved for marketing": "l",
}

# url filter: rslt
clinical_trials_study_results = {
    "All Studies": "",
    "Studies With Results": "With",
    "Studies Without Results": "Without",
}

### CLINICAL TRIALS SEARCH FIELDS OPTIONS #####
OTHER_TERMS = "Other terms"
CONDITION_AND_DISEASE = "Condition/disease"
INTERVENTIOO_TREAMENT = "Intervention/treatment"
LOCATION = "Location"


### FDA MAUDE SEARCH FIELDS OPTIONS #####
PRODUCT_CODE = "Product Code"
MANUFACTURER = "Manufacturer"
MODEL_NUMBER = "Model Number"
REPORT_NUMBER = "Report Number"
BRAND_NAME = "Brand Name"














