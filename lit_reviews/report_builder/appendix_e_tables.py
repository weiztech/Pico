
from lit_reviews.models import *
from django.db.models import Q
from lit_reviews.report_builder.utils import clear_special_characters

def maude_ae_summary_table(lit_review_id, db_obj, date_of_search, date_end):

    
    death = AdverseEvent.objects.filter(
        ae_reviews__search__literature_review__id=lit_review_id,
        event_type="Death",
        # event_date__gte=date_end, 
        # event_date__lte=date_of_search,
        db=db_obj,
    ).count()
    injury = AdverseEvent.objects.filter(
        ae_reviews__search__literature_review__id=lit_review_id,
        event_type="Injury",
        # event_date__gte=date_end, 
        # event_date__lte=date_of_search,
        db=db_obj,
    ).count()
    malfunction = AdverseEvent.objects.filter(
        ae_reviews__search__literature_review__id=lit_review_id,
        event_type="Malfunction",
        db=db_obj,
        # event_date__gte=date_end, 
        # event_date__lte=date_of_search
    ).count()
    na_other = AdverseEvent.objects.filter(
        Q(ae_reviews__search__literature_review__id=lit_review_id),
        Q(db=db_obj),
        Q(Q(event_type="NA") | Q(event_type="Other")),
        # event_date__gte=date_end, 
        # event_date__lte=date_of_search
    ).count()
    # excluded = AdverseEventReview.objects.filter(
    #     search__literature_review_id=lit_review_id, state="EX", search__db=db_obj,
    #     event_date__gte=date_end, 
    #     event_date__lte=date_of_search
    # ).count()
    excluded = 0 
    print(
        "totals summary: death: {0}, inj: {1}, mal: {2}, naother: {3}, excluded: {4}".format(
            str(death), str(injury), str(malfunction), str(na_other), str(excluded)
        )
    )



    # else:

    #     death = AdverseEvent.objects.filter(
    #         ae_events__literature_review__id=lit_review_id,
    #         event_type="Death",
    #         db=db_obj,
    #     ).count()
    #     injury = AdverseEvent.objects.filter(
    #         ae_events__literature_review__id=lit_review_id,
    #         event_type="Injury",
    #         db=db_obj,
    #     ).count()
    #     malfunction = AdverseEvent.objects.filter(
    #         ae_events__literature_review__id=lit_review_id,
    #         event_type="Malfunction",
    #         db=db_obj,
    #     ).count()
    #     na_other = AdverseEvent.objects.filter(
    #         Q(ae_events__literature_review__id=lit_review_id),
    #         Q(db=db_obj),
    #         Q(Q(event_type="NA") | Q(event_type="Other")),
    #     ).count()
    #     excluded = AdverseEventReview.objects.filter(
    #         search__literature_review_id=lit_review_id, state="EX", search__db=db_obj
    #     ).count()

    #     print(
    #         "totals summary: death: {0}, inj: {1}, mal: {2}, naother: {3}, excluded: {4}".format(
    #             str(death), str(injury), str(malfunction), str(na_other), str(excluded)
    #         )
    #     )
    


    row = {
        "Date of Search": str(date_of_search),
        "Date End": str(date_end),
        "Database": db_obj.name,
        "Death": death,
        "Injury": injury,
        "Malfunction": malfunction,
        "Other/NA": na_other,
        "Excluded": excluded,
    }


    return row

def included_aes(lit_review_id, db_obj, date_of_search, date_end):


    all_maude_ars = AdverseEventReview.objects.filter(search__literature_review_id=lit_review_id,
            search__db=db_obj,
            # ae__event_date__gte=date_end,
            # ae__event_date__lte=date_of_search,
            search__db__entrez_enum='maude',
            state='IN',
            ).prefetch_related('ae', 'search').exclude(state='DU').order_by("ae__event_date")
    rows = []
    for ar in all_maude_ars:

        row = {

            "Manufacturer" : ar.ae.manufacturer,
            "Term": ar.search.term,
            "Event Type": ar.ae.event_type,
            "Description": clear_special_characters(ar.ae.description),
        }

        print("writing row {0}".format(row))
        rows.append(row)

    return rows


def maude_aes_by_year(lit_review_id, db_obj, date_of_search, date_end):
            
    # original 
    # ae_events = AdverseEvent.objects.filter(
    #         ae_events__literature_review__id=lit_review_id,
    #         event_date__gte=date_end,
    #         event_date__lte=date_of_search,
    #     )

    ## more precise to use ARs and remove duplicates
    all_maude_ars = AdverseEventReview.objects.filter(search__literature_review_id=lit_review_id,
            # ae__event_date__gte=date_end,
            # ae__event_date__lte=date_of_search,
            search__db__entrez_enum='maude',
            ).prefetch_related('ae', 'search').exclude(state='DU')

    ae_events = []

    for ar in all_maude_ars:
        ae_events.append(ar.ae)

    print("Ae events found {0}".format(len(ae_events)))

    ae_years = {}

    for event in ae_events:
        try:
            ae_years[event.report_date.year].append(event)
        except Exception as e:
            try:
                ae_years[event.report_date.year] = [event]
            except Exception as e:
                try:
                    ae_years[event.event_date.year] = [event]
                except Exception as e:
                    print("Exception processing year for AE event {0} - skipping".format(event))

    # print("init year table for dic {0}".format(ae_years))
    print("ae years keys {0}".format(list(ae_years.keys()).sort()))
    

    years = list(ae_years.keys())
    years.sort()
    
    rows = []
    for year in years:
        death = AdverseEvent.objects.filter(
            ae_reviews__search__literature_review__id=lit_review_id,
            event_type="Death",
            db=db_obj,
            report_date__year=year,
        ).count()
        injury = AdverseEvent.objects.filter(
            ae_reviews__search__literature_review__id=lit_review_id,
            db=db_obj,
            event_type="Injury",
            report_date__year=year,
        ).count()
        malfunction = AdverseEvent.objects.filter(
            ae_reviews__search__literature_review__id=lit_review_id,
            db=db_obj,
            event_type="Malfunction",
            report_date__year=year,
        ).count()
        na_other = AdverseEvent.objects.filter(
            Q(ae_reviews__search__literature_review__id=lit_review_id),
            Q(db=db_obj),
            Q(report_date__year=year),
            Q(Q(event_type="NA") | Q(event_type="Other")),
        ).count()

        
        row = {"Year": str(year), "Deaths": death, "Injuries": injury,
                "Malfunctions": malfunction, "Other/NA": na_other }
        rows.append(row)

    return rows



def all_maude_aes(lit_review_id):
    logger.debug("query for vigilance All Maue AEs")
    logger.warning("WARNING: We are excluding DYB and DQX from this table")
    all_maude_ars = AdverseEventReview.objects.filter(search__literature_review_id=lit_review_id,
        search__db__entrez_enum='maude',
        ).prefetch_related('ae', 'search').exclude(state='DU').exclude(search__term='DYB').exclude(search__term='DQX')

    logger.debug("Total Maude ARs found: {0}".format(len(all_maude_ars)))
    rows = []
    for ar in all_maude_ars:
        row = {
            "Manufacturer" : ar.ae.manufacturer,
            "Term": ar.search.term,
            "Event Type": ar.ae.event_type,
            "Description": ar.ae.description,
        }
        rows.append(row)

    return rows



def maude_recalls_by_year_db_summary(lit_review_id, db_obj):


    recall_reviews = AdverseRecallReview.objects.filter(
        search__literature_review_id=lit_review_id,
        search__db__entrez_enum='maude_recalls'
    )

    print("recall events found {0}".format(recall_reviews.count()))
    ae_years = {}

    for recall in recall_reviews:
        if recall.ae.event_date:
            try:
                ae_years[recall.ae.event_date.year].append(recall.ae)
            except KeyError as e:
                ae_years[recall.ae.event_date.year] = [recall.ae]
        else:
            if ae_years.get(None):
                ae_years[None].append([recall.ae])
            else:
                ae_years[None] = [recall.ae]

    # print("init year table for dic {0}".format(ae_years))
    print("ae years keys {0}".format(list(ae_years.keys()).sort(key=str)))

    years = list(ae_years.keys())
    years.sort(key=str)
    print("appendix e years breakdown of recalls")
    rows = []
    for year in years:

        one = AdverseRecall.objects.filter(
            ae_recalls__literature_review__id=lit_review_id,
            recall_class=1,
            db=db_obj,
            event_date__year=year,
        ).count()
        two = AdverseRecall.objects.filter(
            ae_recalls__literature_review__id=lit_review_id,
            db=db_obj,
            recall_class=2,
            event_date__year=year,
        ).count()
        three = AdverseRecall.objects.filter(
            ae_recalls__literature_review__id=lit_review_id,
            db=db_obj,
            recall_class=3,
            event_date__year=year,
        ).count()

        year_str = str(year) if year else "Unknown"
        row = {
            "Year": year_str,
            "Recall Class 1": one,
            "Recall Class 2": two,
            "Recall Class 3": three,
        }
        rows.append(row)


    return rows


def maude_included_recalls(lit_review_id, date_of_search, date_end):
    all_maude_ars = AdverseRecallReview.objects.filter(search__literature_review_id=lit_review_id,
            ae__event_date__gte=date_end,
            ae__event_date__lte=date_of_search,
            search__db__entrez_enum='maude_recalls',
            state='IN',
            ).prefetch_related('ae', 'search').exclude(state='DU')
    rows = []

    for ar in all_maude_ars:

        row = {

            "Event Date" : ar.ae.event_date,
            "Term": ar.search.term,
            "Recall Class": ar.ae.recall_class,
            "Recall Reason": ar.ae.recall_reason,
        }

        print("writing row {0}".format(row))
        rows.append(row)

    return rows

def all_maude_recalls(lit_review_id):
    all_maude_ars = AdverseRecallReview.objects.filter(
        search__literature_review_id=lit_review_id,
        search__db__entrez_enum='maude_recalls',
    ).prefetch_related('ae', 'search').exclude(state='DU')
    rows = []
    for ar in all_maude_ars:
        row = {

            "Event Date" : ar.ae.event_date,
            "Term": ar.search.term,
            "Recall Class": ar.ae.recall_class,
            "Recall Reason": ar.ae.recall_reason,
        }
        logger.debug("writing row {0}".format(row))
        rows.append(row)

    return rows

def all_manual_aes(lit_review_id):
    aes = AdverseEventReview.objects.filter(
        search__literature_review_id=lit_review_id,
    ).prefetch_related('ae', 'search').exclude(state='DU').exclude(search__db__entrez_enum='maude')
    rows = []

    for ar in aes:
        row = {
            "Database": ar.search.db.name,
            "Event Date" : ar.ae.event_date if ar.ae.event_date else "NA",
            "Term": ar.search.term,
            "Type": ar.ae.manual_type,
            "Severity": ar.ae.manual_severity,
        }
        logger.debug("writing row {0}".format(row))
        rows.append(row)

    return rows

def all_manual_recalls(lit_review_id):
    recalls = AdverseRecallReview.objects.filter(
        search__literature_review_id=lit_review_id,
    ).prefetch_related('ae', 'search').exclude(state='DU').exclude(search__db__entrez_enum='maude_recalls')
    rows = []

    for ar in recalls:
        row = {
            "Database": ar.search.db.name,
            "Event Date" : ar.ae.event_date if ar.ae.event_date else "NA",
            "Term": ar.search.term,
            "Type": ar.ae.manual_type,
            "Severity": ar.ae.manual_severity,
        }
        logger.debug("writing row {0}".format(row))
        rows.append(row)

    return rows


######## END MAUDE FUNCTIONS ########
##########################################

def aes_by_database(lit_review_id, db, is_vigilance):
    print("building appendix e table for database: " + str(db))
    ae_searches = LiteratureSearch.objects.filter(
        literature_review__id=lit_review_id, db__name=db
    ).prefetch_related("ae_events")

    
    ae_table = cite_word.init_table(table_col_names)
    ae_table.style = "Table Grid"
    for ae_search in ae_searches:

        # writer.writerow({"": ae_search.product_code })
        #events = ae_search.ae_events.all()
        
        if is_vigilance:
            events = AdverseEvent.objects.filter(

                ae_events__literature_review__id=lit_review_id,
                ae_events__db=ae_search.db,
                ae_events__term=ae_search.term,
                event_date__gte=date_end,
                event_date__lte=date_of_search
                #ae_events__id=ae_search.id
            ).order_by("event_type")

        else:
            events = AdverseEvent.objects.filter(

                ae_events__literature_review__id=lit_review_id,
                ae_events__db=ae_search.db,
                ae_events__term=ae_search.term,
                #ae_events__id=ae_search.id
            ).order_by("event_type")

        print("events found: " + str(len(events)))

        for ae in events:

            row = {
                "Manufacturer": ae.manufacturer,
                "Code": ae_search.term,
                "Type": ae.event_type,
                "Event ID, Description": ae.description,
            }

            writer.writerow(row)

            row = [
                ae.manufacturer,
                ae_search.term,
                ae.event_type,
                ae.description,
            ]
            cite_word.add_table_row(ae_table, row)


def included_aes_by_database(lit_review_id, db, date_of_search, date_end):

    included_ars = AdverseEventReview.objects.filter(search__literature_review_id=lit_review_id,
        # ae__event_date__gte=date_end,
        # ae__event_date__lte=date_of_search,
        search__db=db,
        state='IN',
        ).prefetch_related('ae', 'search').exclude(state='DU')


    rows = []
    for ar in included_ars:


        row = {


            "Term": ar.search.term,  
            "Date": ar.ae.event_date,  
            "Type": ar.ae.manual_type,
            "Severity": ar.ae.manual_severity

        }

        rows.append(row)
    return rows


def included_recalls_by_database(lit_review_id, db, date_of_search, date_end):

    included_ars = AdverseRecallReview.objects.filter(search__literature_review_id=lit_review_id,
        ae__event_date__gte=date_end,
        ae__event_date__lte=date_of_search,
        search__db=db,
        state='IN',
        ).prefetch_related('ae', 'search').exclude(state='DU')


    rows = []
    for ar in included_ars:


        row = {


            "Term": ar.search.term,  
            "Date": ar.ae.event_date,  
            "Type": ar.ae.manual_type,
            "Severity": ar.ae.manual_severity

        }

        rows.append(row)
    return rows