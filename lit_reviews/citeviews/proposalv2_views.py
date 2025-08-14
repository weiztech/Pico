from django.shortcuts import render
from lit_reviews.custom_permissions import protected_project

@protected_project
def search_terms(request, id):
    return render(request, "lit_reviews/search_terms.html")

def convert_db_name(db_name):
    print("convert db name, passed: " + str(db_name))
    db_name = db_name.lower().strip()

    if db_name == "pubmed central" or db_name == "pmc":
        return "pmc"
    elif db_name == "pubmed":
        print("returning pubmed entrez_enum")
        return "pubmed"

    return db_name