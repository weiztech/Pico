import re 
from unidecode import unidecode

from backend.logger import logger
from lit_reviews.models import (
    LiteratureSearch, 
    LiteratureReviewSearchProposal, 
    ArticleReview,
    ClinicalLiteratureAppraisal,
    NCBIDatabase,
    FinalReportConfig,
    ExtractionField
)
from django.db.models import Q
import collections

from lit_reviews.helpers.articles import get_or_create_appraisal_extraction_fields

def set_unknowns(row):

    for key in row.keys():
        if row[key] == None or row[key] == "":
            row[key] = "Unk"

        row[key] = "Yes" if row[key] is True else row[key]
        row[key] = "No" if row[key] is False else row[key]

    return row


def get_grade_score(lit_appraisal):
    grade_primary = lit_appraisal.grade_primary

    # if grade_primary is None:
    #     raise Exception(
    #         "Missing grade primary for appraisal {0}".format(lit_appraisal.id)
    #     )

    if grade_primary:
        grade_scores = {"VERY LOW": 1, "LOW": 2, "MODERATE": 3, "HIGH": 4, "VERY HIGH": 5}

        grade_likely = {
            None: 0,
            "LIKELY": -1,
            "VERY LIKELY": -2,
        }

        grade_serious = {
            None: 0,
            "SERIOUS": -1,
            "VERY SERIOUS": -2,
        }

        grade_score = grade_scores[grade_primary]
        #print("init grade score {0}".format(grade_score))

        grade_score += grade_likely[lit_appraisal.grade_risk_bias]
        grade_score += grade_serious[lit_appraisal.grade_imprecision]
        grade_score += grade_serious[lit_appraisal.grade_rct_incon]
        grade_score += grade_serious[lit_appraisal.grade_indir]
        grade_score += grade_serious[lit_appraisal.grade_rct_limit]

        return grade_score


def validate_search_terms(lit_review_id):
    not_ae  = Q (Q(is_ae=False) | Q(is_ae__isnull=True))
    not_recall  = Q (Q(is_recall=False) | Q(is_recall__isnull=True))

    dbs = NCBIDatabase.objects.filter(Q(not_ae & not_recall)).exclude(entrez_enum="embase")
    term_counts_nonzero = []
    for db in dbs:
        terms_count = LiteratureSearch.objects.filter(literature_review__id=lit_review_id, db=db).count()
        if terms_count > 0:
            item = (db.entrez_enum, terms_count)
            term_counts_nonzero.append(item)

    summary = "There is a Mismatching Term Count!  Terms Count Summary:  \n <br />"
    for term in term_counts_nonzero:
        summary += f"{term[0]}: {term[1]} \n, <br />"
    summary += "\n <br /> Correct?"
    #print(summary)

    for item1 in term_counts_nonzero:
        for item2 in term_counts_nonzero:
            if item1[1] != item2[1]:

                ## now we need to figure out which terms are mismatched.

                db1 = NCBIDatabase.objects.get(entrez_enum=item1[0])
                db2 = NCBIDatabase.objects.get(entrez_enum=item2[0])


                term_list1 = LiteratureSearch.objects.filter(literature_review__id=lit_review_id, db=db1).values('term')
                term_list2 = LiteratureSearch.objects.filter(literature_review__id=lit_review_id, db=db2).values('term')

                mismatch_terms = []
                for term in term_list1:
                    if term not in term_list2:
                        mismatch_terms.append(term.get("term"))

                for term in term_list2:
                    if term not in term_list1:
                        mismatch_terms.append(term.get("term"))

                error_msg = str(summary + "<br /> Mismatch terms are : " + ", ".join(mismatch_terms))
                raise Exception(error_msg[0:1000] )

    for db in dbs:
        searchs = LiteratureSearch.objects.filter(literature_review__id=lit_review_id, db=db)
        stripped_searchs = [search.term.lower().strip() for search in searchs]
        duplicates = [item for item, count in collections.Counter(stripped_searchs).items() if count > 1]

        if len(duplicates) > 0:
            error = "two or multiple searches for " + db.entrez_enum + " database have same value: " + ", ".join(duplicates)
            raise Exception(error[0:1000])


def validate_report(lit_review_id):
    # this will do sanity checks on a few things

    print("Validating Report...")

    print("syncing all Searches with their SoTA status...")

    searches = LiteratureSearch.objects.filter(literature_review__id=lit_review_id)

    for search in searches:

        props = LiteratureReviewSearchProposal.objects.filter(
            literature_review__id=lit_review_id, term=search.term
        )

        if props.count() > 0:
            is_sota_term = props[0].is_sota_term

            for prop in props:
                if prop.is_sota_term != is_sota_term:
                    print("{0} - {1}".format(prop.id, prop.term))
                    raise Exception(
                        "mismatch of Sota term configuration in Search Terms App"
                    )

        search.save()

    print("...Done!")

    # a = input('stop')

    ## TODO
    ### check all search term counts are equial
    validate_search_terms(lit_review_id)
    
    ## are all articleReview objects with feedback.

    incomplete_reviews = ArticleReview.objects.filter(
        Q(search__literature_review_id=lit_review_id) & Q(Q(state="M") | Q(state="U"))
    )

    if len(incomplete_reviews) > 0:

        error_messages = []
        for rev in incomplete_reviews:
            
            msg = "Review missing for https://app.citemedical.com/literature_reviews/article_review/{0}?back=/literature_reviews/{1}/articles/excluded".format(
                    rev.id, lit_review_id
            )
            print(msg)
            error_messages.append(msg)

        raise Exception("Missing Reviews: " + str(error_messages))

    exclusions_without_reason = ArticleReview.objects.filter(
        Q(search__literature_review_id=lit_review_id)
        & Q(Q(state="E") & Q(Q(exclusion_reason=None) | Q(exclusion_reason="")))
    )

    if len(exclusions_without_reason) > 0:

        error_messages = []
        for rev in exclusions_without_reason:
            
            msg = "Reason missing for exclusion: https://app.citemedical.com/literature_reviews/article_review/{0}?back=/literature_reviews/{1}/articles/excluded".format(
                    rev.id, lit_review_id
                )
            print(msg)
            error_messages.append(msg)
        raise Exception('Excluded Reviews Without Reason: ' + str(error_messages))

    else:
        print("All exclusions have a reason, continuing...")

    ## included appraisals (Device) that are incomplete


    report_config = FinalReportConfig.objects.get(literature_review_id=lit_review_id )
##### Retained Reviews Validations
### This will work, but will take a long time to write for each field...
    
    ar_validation = {}
    base_query =  ArticleReview.objects.filter(
                            Q(
                                Q(search__literature_review_id=lit_review_id) &
                                Q(state='I') &
                                Q(clin_lit_appr__included=True) &
                                Q(clin_lit_appr__is_sota_article=False)
                            ) )
    appropriate_device_inc = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    ar_validation['appropriate_device'] = appropriate_device_inc 

## start here 
    appropriate_application = base_query.filter( Q(clin_lit_appr__appropriate_application=None)) if report_config.appropriate_application else []
    ar_validation['appropriate_application'] = appropriate_application 

    appropriate_patient_group = base_query.filter( Q(clin_lit_appr__appropriate_patient_group=None)) if report_config.appropriate_patient_group else []
    ar_validation['appropriate_patient_group'] = appropriate_patient_group 
    
    acceptable_collation_choices = base_query.filter( Q(clin_lit_appr__acceptable_collation_choices=None)) if report_config.acceptable_collation_choices else []
    ar_validation['acceptable_collation_choices'] = acceptable_collation_choices 
    
    data_contribution = base_query.filter( Q(clin_lit_appr__data_contribution=None)) if report_config.data_contribution else []
    ar_validation['data_contribution'] = data_contribution 


    ## yes nos 
    # design_yn 
    #     outcomes_yn 
    # followup_yn
    # stats_yn
    # study_size_yn
    # clin_sig_yn
    # clear_conc_yn


    ## long form fields  TODO IMPLEMENT VALIDATIO NCHECKS FOR THIS. 
## THESe need to be gone through and updated to match the right field names.... removing appropriate_device references 


    safety = base_query.filter( Q(clin_lit_appr__safety=None) | Q(clin_lit_appr__safety__exact='')) if report_config.safety else []
    ar_validation['safety'] = safety 
    

    # performance = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 

    # adverse_events = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # sota = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # guidance = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # other = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # study_design = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # total_sample_size = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # objective= base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # treatment_modality = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    
    # study_conclusions = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 


    # ## outcomes fields 
    # data_contribution = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 
    # # outcome_measures
    # # appropriate_followup
    # # statistical_significance
    # # clinical_significance

    # justification = base_query.filter( Q(clin_lit_appr__appropriate_device=None)) if report_config.appropriate_device else []
    # ar_validation['appropriate_device'] = appropriate_device_inc 


    for key in ar_validation.keys():

        if len(ar_validation[key]) > 0:

            ## we have an error included AR with missing field.
            raise Exception('Missing Field for Clin Appraisal: {0} - Ids: {1}'.format(key, list(ar_validation[key].values_list('id', flat=True))))



    retained_reviews = ArticleReview.objects.filter(
        Q(
            Q(search__literature_review_id=lit_review_id)
            & Q(state="I")
            & Q(clin_lit_appr__included=True)
            & Q(clin_lit_appr__is_sota_article=False)
        )
        & Q(
            Q(clin_lit_appr__appropriate_device=None)
            | Q(clin_lit_appr__appropriate_application=None)
            | Q(clin_lit_appr__appropriate_patient_group=None)
            | Q(clin_lit_appr__acceptable_collation_choices=None)
            | Q(clin_lit_appr__data_contribution=None)
            |
            # Q(clin_lit_appr__outcome_measures=None) |
            # Q(clin_lit_appr__appropriate_followup=None) |
            # Q(clin_lit_appr__statistical_significance=None) |
            # Q(clin_lit_appr__clinical_significance=None) |
            Q(clin_lit_appr__included=None)
            | Q(clin_lit_appr__justification=None)
            | Q(clin_lit_appr__grade_primary=None)
            # Q(clin_lit_appr__justification="")
        )
    )




    print("lenght of double yes that are incomplete: " + str(retained_reviews))
    if len(retained_reviews) > 0:
        for rev in retained_reviews:
            clin_review = ClinicalLiteratureAppraisal.objects.get(
                article_review__id=rev.id
            )
            print("Clinical Appraisal Mising, ID: " + str(clin_review.id))

    missing_sota_declaration = ArticleReview.objects.filter(
        Q(
            Q(search__literature_review_id=lit_review_id)
            & Q(state="I")
            & Q(clin_lit_appr__included=True)
        )
        & Q(Q(clin_lit_appr__is_sota_article=None))
    )

    if len(missing_sota_declaration) > 0:
        for item in missing_sota_declaration:
            clin_review = ClinicalLiteratureAppraisal.objects.get(
                article_review__id=item.id
            )

            print(
                "Missing Sota Declaration (yes or no) https://app.citemedical.com/literature_reviews/clinical_literature_appraisal/{0}".format(
                    clin_review.id
                )
            )

    if report_config.grade:

        missing_grades = ArticleReview.objects.filter(
            Q(
                Q(search__literature_review_id=lit_review_id)
                & Q(state="I")
                & Q(clin_lit_appr__included=True)
                & Q(clin_lit_appr__is_sota_article=False)
                & Q(clin_lit_appr__grade_primary=None)
            )
        )

        if len(missing_grades) > 0:
            for g in missing_grades:
                clin_review = ClinicalLiteratureAppraisal.objects.get(
                    article_review__id=g.id
                )

                print(
                    "Missing GRADE eval for included appraisal https://app.citemedical.com/literature_reviews/clinical_literature_appraisal/{0}".format(
                        clin_review.id
                    )
                )

    ## check for missing citations

    article_reviews = ArticleReview.objects.filter(
        Q(
            Q(search__literature_review_id=lit_review_id)
            & Q(Q(article__citation=None) | Q(article__citation=""))
        )
    )

    ## check for included articles that are missing

    if len(article_reviews) > 0:

        error_messages = []
        for ar in article_reviews:
            msg = "Citation Missing for Article " + str(ar.article.id)
            error_messages.append(ar.article.id)
        raise Exception("Citations Missing! Check with team: " + str(error_messages))



#### Validations for AE reviews

## 1.  do all dbs either have data or are marked as completed?


######

    print("validation complete!")


def get_db_list(lit_review_id, db_type):

    literature_searches = LiteratureSearch.objects.filter(
            literature_review__id=lit_review_id
        )
    if db_type == 'lit':    

        literature_searches = literature_searches.exclude(db__is_recall=True).exclude(db__is_ae=True)
       
    elif db_type == 'ae':

        literature_searches = literature_searches.filter(db__is_ae=True).exclude(db__entrez_enum='maude')

    elif db_type == 'recall':

        literature_searches = literature_searches.filter(db__is_recall=True).exclude(db__entrez_enum='maude_recalls')


    dbs = list(
            set(
                literature_searches.values_list("db")
            )
    )

    dbs_list = []
    for tup in dbs:
        dbs_list.append(tup[0])

    print("db list returned: {0}".format(dbs_list))
    return dbs_list


def clear_special_characters(value):
    # # remove diacritics used to replace specail characters like ü with u or ó with o ...
    # value = unidecode(value)

    # non_html_string = re.sub('</*[a-z]+>|;',' ', value)
    # return re.sub('[^a-zA-Z0-9.!:\-\*\?_,();  *]+',' ', non_html_string)
    """
    Clear special characters from a string.
    Above implimentation is no longer required since now we're using escape=true 
    when rendering the context to the Docx Template.
    This is only from clearing XML like context ex: <i>.
    """
    return re.sub('</*[a-z]+>|;',' ', value)


def construct_appraisal_data_contribution(appraisal, review_id):
    contribution_list = {
        "design_yn": {"symbole": "T"},
        # "outcomes_yn": {"symbole": "O"},
        # "followup_yn": {"symbole": "F"},
        # "stats_yn": {"symbole": "S"},
        # "clin_sig_yn": {"symbole": "C"},
    }

    extraction_fields = ExtractionField.objects.filter(field_section="QC", literature_review__id=review_id)
    output = []
    for extraction in extraction_fields:
        app_extraction_field = get_or_create_appraisal_extraction_fields(appraisal, extraction)
        value = "1" if app_extraction_field.value.lower() == "yes" else "2"
        if extraction.name in contribution_list.keys():
            extraction_output = contribution_list[extraction.name]["symbole"] + value
        else:
            extraction_output = extraction.name[0].upper() + value
        output.append(extraction_output)
    return ", ".join(output)

SUITABILITY_VALUES_SYMBOLES = {
    "appropriate_device": {"Actual Device": "D1", "Similar Device": "D2", "Other Device": "D3"},
    "appropriate_application": {"Same Use": "A1", "Minor Deviation": "A2", "Major Deviation": "A3"},
    "appropriate_patient_group": {"Applicable": "P1", "Limited": "P2", "Different Population": "P3"},
    "acceptable_collation_choices": {"High Quality": "R1", "Minor Deficiencies": "R2", "Insufficient Information": "R3"},
}

def construct_appraisal_data_suitability(appraisal, review_id):
    outputs = []
    for extraction_name, symboles in SUITABILITY_VALUES_SYMBOLES.items():
        extraction_field = ExtractionField.objects.filter(name=extraction_name, literature_review__id=review_id).first()
        if extraction_field:
            app_extraction_field = get_or_create_appraisal_extraction_fields(appraisal, extraction_field)
            value = symboles[app_extraction_field.value]
            outputs.append(value)
        else:
            logger.warning("Extraction field name {extraction_name} for lit review with id {review_id}")

    return ", ".join(outputs)
