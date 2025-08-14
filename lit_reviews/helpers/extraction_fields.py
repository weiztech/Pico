from lit_reviews.models import (
    ExtractionField,
    ClinicalLiteratureAppraisal,
)
from lit_reviews.helpers.articles import get_or_create_appraisal_extraction_fields
from backend.logger import logger
import json 

extraction_fields_names = [
    {"name": "device_name", "type": "TEXT", "category": "T", "field_order": 4},
    {"name": "indication", "type": "TEXT", "category": "T", "field_order": 5},
    {"name": "study_conclusions", "type": "LONG_TEXT", "category": "SR", "field_order": 12},
    {"name": "treatment_modality", "type": "LONG_TEXT", "category": "T", "field_order": 9},
    {"name": "objective", "type": "LONG_TEXT", "category": "ST", "field_order": 2},
    {"name": "total_sample_size", "type": "LONG_TEXT", "category": "ST", "field_order": 3},
    {"name": "study_design", "type": "LONG_TEXT", "category": "ST", "field_order": 1},
    {"name": "other", "type": "LONG_TEXT", "category": "ST", "field_order": 11},
    {"name": "adverse_events", "type": "LONG_TEXT", "category": "SR", "field_order": 8},
    {"name": "performance", "type": "LONG_TEXT", "category": "SR", "field_order": 6},
    {"name": "safety", "type": "LONG_TEXT", "category": "SR", "field_order": 7},
]

######## Suitability and Outcomes ##########
suitability_and_outcomes_names = [
    {
        "name": "appropriate_device", 
        "type": "DROP_DOWN",
        "name_in_report": "Device",
        "values": [
            "Actual Device",
            "Similar Device",
            "Other Device",
        ],
    },
    {
        "name": "appropriate_application", 
        "type": "DROP_DOWN",
        "name_in_report": "Application",
        "values": [
            "Same Use",
            "Minor Deviation",
            "Major Deviation",
        ],
    },
    {
        "name": "appropriate_patient_group", 
        "type": "DROP_DOWN",
        "name_in_report": "Population",
        "values": [
            "Applicable",
            "Limited",
            "Different Population",
        ],
    },
    {
        "name": "acceptable_collation_choices", 
        "type": "DROP_DOWN",
        "name_in_report": "Report",
        "values": [
            "High Quality",
            "Minor Deficiencies",
            "Insufficient Information",
        ],
    },
    # {
    #     "name": "data_contribution", 
    #     "type": "DROP_DOWN",
    #     "values": [
    #         "Yes (Expert Opinion)",
    #         "Yes (Review Article)",
    #         "Yes (Questionnaire)",
    #         "Yes",
    #         "No",
    #     ],
    # },
]

############ Quality and Contribution Questions #############
quality_and_contribution_names = [
    {"name": "design_yn", "type": "DROP_DOWN", "description": "Was the design of the study appropriate?"}, 
    {"name": "outcomes_yn", "type": "DROP_DOWN", "description": "Do the outcome measures reported reflect the intended performance of the device?"},
    {"name": "followup_yn", "type": "DROP_DOWN", "description": "Is the duration of follow-up long enough to assess whether duration of treatment effects and identify complications?"},
    {"name": "stats_yn", "type": "DROP_DOWN", "description": "Has a statistical analysis of the data been provided and is it appropriate?"},
    {"name": "clin_sig_yn", "type": "DROP_DOWN", "description": "Was the magnitude of the treatment effect observed clinically significant?"},
]

######## SoTA ##########
sota_names = [
    {
        "name": "sota_suitability", 
        "name_in_report": "SoTA Classification",
        "type": "DROP_DOWN",
        "values": [
            "CK0 No SoTA Information",
            "CK1 Establishment of current knowledge/ the state of the art on the medical condition",
            "CK2 Establishment of current knowledge/ the state of the art on alternative therapies/treatments",
            "CK3 Determination and justification of criteria for the evaluation of the risk/benefit relationship",
            "CK4 Determination and justification of criteria for the evaluation of acceptability of undesirable side-effects",
            "CK5 Determination of equivalence",
            "CK6 Justification of the validity of surrogate endpoints",
        ],
    },
    {
        "name": "sota_exclusion_reason", 
        "name_in_report": "Exclusion Reason",
        "type": "DROP_DOWN",
        "values": [
            "Describes technical or non-clinical study results only, including animal or cadaver studies",
            "Contains unsubstantiated opinions",
            "Do not represent the current knowledge/state of the art",
            "Articles is older than 5 years",
            "Non-English Language",
            "Publications types other than Peer reviewed guidelines, International peer reviewed consensus statements, State of the Art review (can be narrative review), systematic review, or Meta-Analysis",
        ],
    },
]

# create MDCG Raning 
MDCG_names = {
    "name": "mdcg_ranking",
    "type": "DROP_DOWN",
    "drop_down_values": json.dumps([
        "Rank 01", "Rank 02", "Rank 03", "Rank 04", "Rank 05", "Rank 06", "Rank 07", "Rank 08", "Rank 09", "Rank 10", "Rank 11", "Rank 12"
    ]),
    "field_section": "MR",
}


Extractions_AI_Prompts = {
    "device_name": "Extract device name",
    "indication": "Extract indication of use",
    "study_conclusions": "Extract the authors' primary conclusions and key findings as stated in the conclusion/discussion section, focusing on statements that directly address the research question or hypotheses.",
    "treatment_modality": "Identify the specific therapeutic approach, intervention, or device application method described in the study, including relevant technical parameters, dosages, or protocols.",
    "objective": "Capture the explicitly stated primary and secondary objectives or aims of the study as written in the introduction or methods section.",
    "total_sample_size": "Extract the exact number of subjects or samples included in the final analysis, noting any discrepancies between enrolled, randomized, and analyzed populations. Provide the final number used in analysis.",
    "study_design": "Identify the specific research methodology employed, including trial type (RCT, observational, etc.), blinding methods, control groups, and duration of follow-up.",
    "adverse_events": "Extract all mentions of complications, side effects, or negative outcomes related to the device or intervention, including severity classifications and frequency data, if available.",
    "performance": "Capture quantitative and qualitative results related to the device's primary function and effectiveness, including success rates, procedural outcomes, and technical performance metrics.",
    "safety": "Extract information specifically addressing the safety profile of the device or intervention, including biocompatibility data, device-related complications, and any safety-specific analyses.",
}


def create_extractions(lit_review):
    logger.info("Creating extraction fields for: {}".format(str(lit_review)))        
    for extractin in extraction_fields_names:
        values = {
            "name": extractin["name"],
            "type": extractin["type"],
            "category": extractin["category"],
            "field_order": extractin["field_order"],
            "literature_review": lit_review,
            "field_section": "EF",
        }
        if not ExtractionField.objects.filter(**values).exists():
            ExtractionField.objects.create(**values)
        else:
            logger.warning("Already exists")

def create_suitability_and_outcomes(lit_review):
    logger.info("Creating suitability_and_outcomes( fields for: {}".format(str(lit_review)))        
    for extractin in suitability_and_outcomes_names:
        values = {
            "name": extractin["name"],
            "type": extractin["type"],
            "name_in_report": extractin.get("name_in_report", None),
            "drop_down_values": json.dumps(extractin["values"]),
            "literature_review": lit_review,
            "field_section": "SO",
        }
        if not ExtractionField.objects.filter(**values).exists():
            ExtractionField.objects.create(**values)
        else:
            logger.warning("Already exists")

def create_quality_and_contribution(lit_review):
    logger.info("Creating quality_and_contribution fields for: {}".format(str(lit_review)))  
    yes_no_choices = [
        "Yes",
        "No",
    ]      
    for extractin in quality_and_contribution_names:
        values = {
            "name": extractin["name"],
            "type": extractin["type"],
            "description": extractin["description"],
            "drop_down_values": json.dumps(yes_no_choices),
            "literature_review": lit_review,
            "field_section": "QC",
        }
        if not ExtractionField.objects.filter(**values).exists():
            ExtractionField.objects.create(**values)
        else:
            logger.warning("Already exists")

def create_sota(lit_review):
    logger.info("Creating sota fields for: {}".format(str(lit_review)))      
    for extractin in sota_names:
        values = {
            "name": extractin["name"],
            "type": extractin["type"],
            "name_in_report": extractin.get("name_in_report", None),
            "drop_down_values": json.dumps(extractin["values"]),
            "literature_review": lit_review,
            "field_section": "ST",
        }
        if not ExtractionField.objects.filter(**values).exists():
            ExtractionField.objects.create(**values)
        else:
            logger.warning("Already exists")

def create_and_link_default_extraction_fields(lit_review):
    create_extractions(lit_review)
    create_suitability_and_outcomes(lit_review)
    create_quality_and_contribution(lit_review)
    create_sota(lit_review)

    if not ExtractionField.objects.filter(**MDCG_names, literature_review=lit_review).exists():
        ExtractionField.objects.create(**MDCG_names, literature_review=lit_review)
    else:
        logger.warning("Already exists")
    
    add_literature_review_extractions_prompts(lit_review)


def copy_default_extraction_fields_values(lit_review):
    logger.info("Copying default values for {} appraisals".format(str(lit_review)))
    apps = ClinicalLiteratureAppraisal.objects.filter(article_review__search__literature_review=lit_review)
    for app in apps:
        all_extractions = [*extraction_fields_names, *suitability_and_outcomes_names, *quality_and_contribution_names, *sota_names, MDCG_names]
        for extraction in all_extractions:
            logger.info("Appraisal {}".format(extraction["name"]))
            extraction_field = ExtractionField.objects.get(name=extraction["name"], literature_review=lit_review)
            app_extraction_field = get_or_create_appraisal_extraction_fields(app, extraction_field)
            if extraction["type"] == "DROP_DOWN":
                field_name = extraction["name"]
                app_extraction_field.value = getattr(app, f"get_{field_name}_display")()

            elif extraction["type"] == "NUMBER":
                app_extraction_field.value = getattr(app, extraction["name"])
            else:
                app_extraction_field.value = str(getattr(app, extraction["name"]))
            app_extraction_field.save()
            

def create_ai_prompte_for_extraction_dropdown_type(extraction):
    formated_name = extraction.name.replace("_", " ").title()
    prompt = f"{formated_name} select one of the following choices {extraction.drop_down_values}"
    return prompt    


def add_extraction_ai_prompt(extraction):
    if not extraction.ai_prompte:
        prompt = Extractions_AI_Prompts.get(extraction.name ,None)
        if not prompt and extraction.type == "DROP_DOWN":
            prompt = create_ai_prompte_for_extraction_dropdown_type(extraction)

        if prompt:
            extraction.ai_prompte = prompt
            extraction.save()
            return prompt
    

def add_literature_review_extractions_prompts(lit_review):
    extraction_fields = ExtractionField.objects.filter(literature_review=lit_review)    
    for extraction in extraction_fields:
        add_extraction_ai_prompt(extraction)