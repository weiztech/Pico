from backend.logger import logger
from lit_reviews.models import (
    AdverseEventReview,
    AdverseRecallReview,
)

def appendix_e2_report_context(lit_review_id, type="maude_ae"):
    row_list = []

    if type == "maude_ae":
        header = ["Manufacturer", "Term", "Event Type","Description"]
        row_list.append(header)
        
        try:
            all_maude_ars = AdverseEventReview.objects.filter(search__literature_review_id=lit_review_id,
                search__db__entrez_enum='maude',
            ).prefetch_related('ae', 'search').exclude(state='DU').exclude(search__term='DYB').exclude(search__term='DQX')
            
            for ar in all_maude_ars:
                row=[]
                row.append(ar.ae.manufacturer)
                row.append(ar.search.term)
                row.append(ar.ae.event_type)
                row.append(ar.ae.description)
                row_list.append(row)

            return row_list

        except Exception as e:
            logger.error("Appendix E2 Context Error generating maude aes: {0}".format(str(e)))
            raise e
        
    elif type == "maude_recalls":
        header = ["Event Date", "Term", "Recall Class","Recall Reason"]
        row_list.append(header)
        
        try:
            all_maude_ars = AdverseRecallReview.objects.filter(
                search__literature_review_id=lit_review_id,
                search__db__entrez_enum='maude_recalls',
            ).prefetch_related('ae', 'search').exclude(state='DU')
            for ar in all_maude_ars:
                row = []
                row.append(ar.ae.event_date) 
                row.append(ar.search.term) 
                row.append(ar.ae.recall_class) 
                row.append(ar.ae.recall_reason) 
                row_list.append(row)

            return row_list

        except Exception as e:
            logger.error("Appendix E2 Context Error generating maude recalls: {0}".format(str(e)))
            raise e
        

    elif type == "manual_aes":
        header = ["Database", "Event Date", "Term", "Type","Severity"]
        row_list.append(header)
        
        try:
            aes = AdverseEventReview.objects.filter(
                search__literature_review_id=lit_review_id,
            ).prefetch_related('ae', 'search').exclude(state='DU').exclude(search__db__entrez_enum='maude')
            for ar in aes:
                row = []
                row.append(ar.search.db.name) 
                row.append(ar.ae.event_date) 
                row.append(ar.search.term) 
                row.append(ar.ae.manual_type) 
                row.append(ar.ae.manual_severity) 
                row_list.append(row)

            return row_list

        except Exception as e:
            logger.error("Appendix E2 Context Error generating manual aes: {0}".format(str(e)))
            raise e
        

    elif type == "manual_recalls":
        header = ["Database", "Event Date", "Term", "Type","Severity"]
        row_list.append(header)
        
        try:
            recalls = AdverseRecallReview.objects.filter(
                search__literature_review_id=lit_review_id,
            ).prefetch_related('ae', 'search').exclude(state='DU').exclude(search__db__entrez_enum='maude_recalls')
            for ar in recalls:
                row = []
                row.append(ar.search.db.name) 
                row.append(ar.ae.event_date) 
                row.append(ar.search.term) 
                row.append(ar.ae.manual_type) 
                row.append(ar.ae.manual_severity) 
                row_list.append(row)

            return row_list

        except Exception as e:
            logger.error("Appendix E2 Context Error generating manual recalls: {0}".format(str(e)))
            raise e