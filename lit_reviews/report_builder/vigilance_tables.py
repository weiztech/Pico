from lit_reviews.models import (
    LiteratureSearch,
    AdverseEventReview,
    NCBIDatabase,
    AdverseEvent,
)
from django.db.models import Q

def vig_annual_maude_counts_by_term(lit_review, maude_db, year, cite_word, included):

    ## columns  search term, death , injury malfunction, other/na

    lit_searches = LiteratureSearch.objects.filter(literature_review=lit_review, db=maude_db)

    if included:

        cite_word.add_hx("Annual Overview of AE Safety Data - Maude - Year {0} - Included Events".format(year ), "CiteH1")

    else:
        cite_word.add_hx("Annual Overview of AE Safety Data - Maude - Year {0} - All Events".format(year ), "CiteH1")



    t_cols = ["Term",  "Death", "Injury", "Malfunction", "Other/NA"]

    t = cite_word.init_table(t_cols)


    for lit_search in lit_searches:


        row = ae_counts_by_search_year_state(lit_search, year, included )

        cite_word.add_table_row(t, row.values())


    return cite_word

def vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term=None, all_records=False):


    print("Building Monthly SUmmary Table for Maude...")
    years = get_ae_years(lit_review, maude_db, date_of_search, date_end, lit_search=None)

    for year in years:

        
        if specific_term and all_records:

            cite_word.add_hx("Monthly Overview of AE Safety Data - Maude {0} Specific Term: {1} - All Events  ".format(year, specific_term), "CiteH1")

        elif specific_term:

            cite_word.add_hx("Monthly Overview of AE Safety Data - Maude {0} Specific Term: {1} - Included Records".format(year, specific_term), "CiteH1")


        elif all_records:

            cite_word.add_hx("Monthly Overview of AE Safety Data - Maude {0}  All Events - Duplicates Removed".format(year), "CiteH1")

        else:

            cite_word.add_hx("Monthly Overview of AE Safety Data - Maude {0} - All Search Terms - TERUMO Included Records - Duplicates Removed ".format(year), "CiteH1")



        t3_cols = ["Year", "Month", "All Terms", "Death", "Injury", "Malfunction", "Other/NA"]

        t3 = cite_word.init_table(t3_cols)


        for index, month in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "July", "Aug", "Sep", "Oct", "Nov", "Dec"]):

            sample_date = date(int(year), index+1, 1)
            if sample_date >= date_end  and sample_date <= date_of_search:
                print("month and year fall within range, so we want the row:")

                counts = ae_counts_by_db_and_month(lit_review.id, maude_db, index+1 , year, all_records=all_records, specific_term=specific_term)
                    #def ae_counts_by_db_and_month(lit_review_id, db_obj, month, year, all_records=False, specific_term=False):

                row = {

                    "Year": year,
                    "Month": month,
                    "All Terms": None,
                    "Death": counts['death'] ,
                    "Injury": counts['injury'],
                    "Malfunction": counts['malfunction'] ,
                    "Other/NA": counts['na_other']
                }

                ## write row to table. 
                cite_word.add_table_row(t3, row.values())

    return cite_word
  #### ########

def vig_all_included_per_db(lit_review_id, date_end, date_of_search, cite_word):
    print("Starting Table 4 in vig report")
    dbs = NCBIDatabase.objects.filter(is_ae=True)

    for db in dbs:


        ae_reviews = AdverseEventReview.objects.filter(search__db=db, state="IN",
                                         ae__event_date__gte=date_end,
                                     ae__event_date__lte=date_of_search,
                                         search__literature_review_id=lit_review_id).prefetch_related('ae')


        cite_word.add_hx("Table 4 Assessment of Relevant Safety Events AE Data - {0}".format(db), "CiteH2")

        t4_cols =  [ "Date", "Search Term", "Adverse Event", "Incident Type", "Relevant AE" ]
        t4 = cite_word.init_table(t4_cols)


        # output_path = "/tmp/"
        # with open(output_path + "terumo_all_included_aes{0}.csv".format(db), "w") as csvfile:


        #     writer = csv.DictWriter(csvfile, fieldnames=t4_cols)
        #     writer.writeheader()

        for aer in ae_reviews:


            row = {

                "Date": aer.ae.event_date ,
                "Search Term": aer.search.term,
                "Adverse Event": aer.ae.description if (db.entrez_enum == 'maude' or db.entrez_enum =='fda_tplc') else aer.ae.manual_severity,
                #"Adverse Event": aer.ae.manual_severity,
                #"Incident Type": aer.ae.manual_type,

                "Incident Type":  aer.ae.event_type if (db.entrez_enum == 'maude' or db.entrez_enum =='fda_tplc') else aer.ae.manual_type,
                "Relevant AE":  "??",
            }

            cite_word.add_table_row(t4, row.values())

             #   writer.writerow(row)
    return cite_word
     ################

### Helper functions -- maybe move these too.


def get_ae_filters(lit_review_id=None):


    ## TODO: get these from db instead of manual input

    device_variations = ['angioseal', 'angio-seal', 'femoseal', 'femo-seal']
    device_variations = []
    descr_or_filter = Q()
    for item in device_variations:

        descr_or_filter |= Q(ae__description__icontains=item)


    manuf_or_filter = Q(Q(ae__manufacturer__icontains='TERUMO') | Q(ae__manufacturer__icontains='ST. JUDE'))

    return descr_or_filter, manuf_or_filter




def ae_counts_by_search_year_state(lit_search, year, included=True):
    print("TODO: Make acceptable for non-maude dbs.")
    print("TODO remove terumo specific logic")
    descr_or_filter, manuf_or_filter = get_ae_filters()

    if included:

        death = AdverseEventReview.objects.filter(

            search=lit_search,
            ae__event_type="Death",
            ae__event_date__year=year,
            #state="IN",
           # ae__manufacturer__icontains='TERUMO'
        )

        death = death.filter( manuf_or_filter).filter(descr_or_filter)

        injury = AdverseEventReview.objects.filter(

            search=lit_search,
            ae__event_type="Injury",
            ae__event_date__year=year,
        #    ae__manufacturer__icontains='TERUMO'

        )

        injury = injury.filter( manuf_or_filter).filter(descr_or_filter)

        malfunction = AdverseEventReview.objects.filter(

            search=lit_search,
            ae__event_type="Malfunction",
            ae__event_date__year=year,
         #   ae__manufacturer__icontains='TERUMO'

        )

        malfunction = malfunction.filter( manuf_or_filter).filter(descr_or_filter)

        na_other = AdverseEventReview.objects.filter(
            Q(search=lit_search),
            Q(Q(ae__event_type="NA") | Q(ae__event_type="Other")),
            Q(ae__event_date__year=year),
        #    Q(ae__manufacturer__icontains='TERUMO'),

        )

        na_other = na_other.filter( manuf_or_filter).filter(descr_or_filter)

    else:

        death = AdverseEventReview.objects.filter(

            search=lit_search,
            ae__event_type="Death",
            ae__event_date__year=year,
            

        )


        injury = AdverseEventReview.objects.filter(

            search=lit_search,
            ae__event_type="Injury",
            ae__event_date__year=year,
        )


        malfunction = AdverseEventReview.objects.filter(

            search=lit_search,
            ae__event_type="Malfunction",
            ae__event_date__year=year,
           

        )


        na_other = AdverseEventReview.objects.filter(
            Q(search=lit_search),
            Q(Q(ae__event_type="NA") | Q(ae__event_type="Other")),
            Q(ae__event_date__year=year),
            

        )

    from lit_reviews.report_builder.appendices import dedupe_individual_search
    death = dedupe_individual_search(death)
    malfunction = dedupe_individual_search(malfunction)
    injury = dedupe_individual_search(injury)
    na_other = dedupe_individual_search(na_other)

    return {
        "term": lit_search.term,
        "death": len(death),
        "injury": len(injury),
        "malfunction": len(malfunction),
        "na_other": len(na_other),
    }



def ae_counts_by_search_and_year(lit_search, year, lit_review_id):
    death = AdverseEvent.objects.filter(
        ae_events__id=lit_search.id,
        event_type="Death",
        db=lit_search.db,
        event_date__year=year,
            
    )

    injury = AdverseEvent.objects.filter( Q(
        Q(ae_events__id=lit_search.id) &
        Q(db=lit_search.db ) &
        Q( Q(event_type="Injury") | Q(manual_severity="Injury")) &
        Q(event_date__year=year) 

        )
    )
    malfunction = AdverseEvent.objects.filter(
        ae_events__id=lit_review_id,
        db=lit_search.db,
        event_type="Malfunction",
        event_date__year=year,
    )
    na_other = AdverseEvent.objects.filter(
        Q(ae_events__id=lit_review_id),
        Q(db=lit_search.db),
        Q(event_date__year=year),
        Q(Q(event_type="NA") | Q(event_type="Other")),
    )

    from lit_reviews.report_builder.appendices import dedupe_individual_search
    death = dedupe_individual_search(death)
    malfunction = dedupe_individual_search(malfunction)
    injury = dedupe_individual_search(injury)
    na_other = dedupe_individual_search(na_other)
    
    return {

        "death": len(death),
        "injury": len(injury),
        "malfunction": len(malfunction),
        "na_other": len(na_other),

    }



def get_ae_years(lit_review, db, date_of_search, date_end, lit_search=None):

    print("inside get_ae_years")
    print("NEED TO CHANGE TO OPTIMIZED QUERY")
 ## example 
 ##    AdverseEventReview.objects.filter(search__literature_review_id=22, search__term='DQX').values('ae__event_date__year').distinct()




    if lit_search:
        adverse_reviews = AdverseEventReview.objects.filter(search=lit_search, 
            ae__event_date__gte=date_end,
             ae__event_date__lte=date_of_search).prefetch_related('ae')

        #ae_events2 = AdverseEvent.objects.filter( ae_events__id=lit_search.id  ).count()
        #print("Ae 2 count {0}".format(ae_events2))

    else:
        adverse_reviews = AdverseEventReview.objects.filter(search__literature_review_id=lit_review.id, search__db=db, ae__event_date__gte=date_end, ae__event_date__lte=date_of_search).prefetch_related('ae')


    ae_events = []
    print("before for loop of all AE Reviews found.")
    for review in adverse_reviews:
        print("apending ae {0}".format(review.ae))
        ae_events.append(review.ae)


    # ae_events = AdverseEvent.objects.filter(
    #         ae_events__literature_review__id=lit_review_id,
    #     )
    print("Ae events found {0}".format(len(ae_events)))

    ae_years = {}

    for event in ae_events:
        try:
            ae_years[event.event_date.year].append(event)
        except KeyError as e:
            ae_years[event.event_date.year] = [event]

    # print("init year table for dic {0}".format(ae_years))
    print("ae years keys {0}".format(list(ae_years.keys()).sort()))
    
    years = list(ae_years.keys())
    years.sort()

    print("returning get_ae_years")

    return years
