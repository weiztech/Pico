from django.urls import include, path
import lit_reviews.citeviews.proposalv2_views as citeviews
import lit_reviews.citeviews.full_text_uploader_views as ftviews
import lit_reviews.search_notebook.views as search_notebook_views
import lit_reviews.citeviews.search_dash as search_dash
import lit_reviews.citeviews.report_builder_dash as report_builder_dash
import lit_reviews.citeviews.articles as articles
import lit_reviews.citeviews.documents_library as documents_library
import lit_reviews.citeviews.exclusion_reason as exclusion_reason
import lit_reviews.citeviews.adverse_events as adverse_events
import lit_reviews.citeviews.products as product
import lit_reviews.citeviews.clinical_literature_appraisal as cl_appraisal
import lit_reviews.citeviews.home as home
import lit_reviews.citeviews.keywords as keywords
import lit_reviews.citeviews.search_lit_review as search_lit
import lit_reviews.citeviews.extraction_fields as extraction_fields

from lit_reviews.citeviews.home import (
    literature_reviews_home, 
    literature_reviews_settings,
    citemed_ms_word_extention,
    living_reviews,
    create_living_review,
    living_review_detail
)


app_name = "lit_reviews"
urlpatterns = [
    # --------------- home views urls ---------------
    path("", literature_reviews_home, name="literature_review_list"),
    path("settings/", literature_reviews_settings, name="literature_reviews_settings"),
    path("living_reviews/", living_reviews, name="living_reviews"),
    path("create_living_review/", create_living_review, name="create_living_review"),
    path("living_reviews/<int:id>/", living_review_detail, name="living_review_detail"),
    path("citemed_ms_word_extention/", citemed_ms_word_extention, name="citemed_ms_word_extention"),
    # path("home/", LiteratureReviewListViewVue, name="literature_review_list_vue"),
    path("<int:id>/", home.literature_review_detail, name="literature_review_detail"),
    path("<int:id>/archive_lit_review/", home.archive_lit_review, name="archive_lit_review"),
    path("create_test_project/", home.create_test_project, name="create_test_project"),
    path("documents_library/",documents_library.documents_library_view,name="documents_library" ),

    # path(
    #     "<int:id>/equivalent_device_discussion",
    #     search_lit.equivalent_device_discussion,
    #     name="equivalent_device_discussion",
    # ),
    path(
        "<int:id>/search_protocol",
        search_lit.search_protocol,
        name="search_protocol",
    ),

    # --------------- searchs views urls ---------------
    path("<int:id>/run_search", search_lit.run_search, name="run_search"),

    # --------------- keywords views urls ---------------
    path("<int:id>/keyword", keywords.keyword, name="keyword"),

    # --------------- articles views urls ---------------
    path(
        "<int:id>/article_review/<int:article_id>",
        articles.article_review_detail,
        name="article_review_detail",
    ),
    path(
        "<int:id>/article_state_change",
        articles.article_state_change,
        name="article_state_change",
    ),
    path(
        "<int:id>/articles/",
        articles.article_reviews_list,
        name="article_reviews_list",
    ),
    path(
        "<int:id>/citation_updater/", 
        articles.citation_updater, 
        name="citation_updater"
    ),
    path(
        "<int:id>/article_tags/", 
        articles.article_tags, 
        name="article_tags"
    ),
    path(
        "<int:id>/duplicates_articles/",
        articles.duplicates_articles,
        name="duplicates_list_url",
    ),
    path(
        "<int:id>/review_article_full_text_pdf/<int:review_id>/",
        articles.review_article_full_text_pdf,
        name="review_article_full_text_pdf",
    ),

    # --------------- search_dash views urls ---------------
    path(
        "<int:id>/search_dashboard",
        search_dash.search_dashboard,
        name="search_dashboard",
    ),
    path(
        "<int:id>/search_terms/", citeviews.search_terms, name="search_terms"
    ),
    
    # --------------- ReportBuilder dash urls ---------------
    path(
        "<int:id>/report_builder",
        report_builder_dash.report_builder,
        name="report_builder",
    ),
    path(
        "<int:id>/exclusion_reason/",
        exclusion_reason.exclusion_reason_list_create,
        name="exclusion_reason",
    ),
    path(
        "<int:id>/exclusion_reason/<int:instance_id>/",
        exclusion_reason.exclusion_reason_update,
        name="exclusion_reason_update",
    ),
    path(
        "<int:id>/exclusion_reason/<int:instance_id>/delete/",
        exclusion_reason.exclusion_reason_delete,
        name="exclusion_reason_delete",
    ),

    # --------------- adverse_events urls ---------------
    path("<int:id>/adverse_database_summary/",
        adverse_events.adverse_database_summary,
        name="adverse_database_summary"
    ),
    path("<int:id>/manual_ae_searches/",
        adverse_events.manual_ae_searches,
        name="manual_ae_searches"
    ),
    path("<int:id>/delete_adverse_event/<int:ae_id>/",
        adverse_events.delete_adverse_event,
        name="delete_adverse_event"
    ),
    path("<int:id>/delete_adverse_recall/<int:ar_id>/",
        adverse_events.delete_adverse_recall,
        name="delete_adverse_recall"
    ),
    path("<int:id>/update_adverse_event/<int:ae_id>/",
        adverse_events.update_adverse_event,
        name="update_adverse_event"
    ),
    path("<int:id>/update_adverse_recall/<int:ar_id>/",
        adverse_events.update_adverse_recall,
        name="update_adverse_recall"
    ),
    path(
        "<int:id>/adverse_event_review/<int:ae_id>",
        adverse_events.adverse_event_review_detail,
        name="adverse_event_review_detail",
    ),
    path("<int:id>/adverse_events", adverse_events.ae_list, name="ae_list"),
    path(
        "adverse_event_review_single/",
        adverse_events.include_single_ae_review,
        name="single_ae_review",
    ),

    # --------------- product urls ---------------
    path("<int:id>/product_details", product.product_details, name="product_details"),
    path(
        "create_literaturereview",
        product.create_literaturereview,
        name="create_literaturereview",
    ),
    # --------------- clinical literature appraisals urls ---------------
    path(
        "<int:id>/clinical_literature_appraisals",
        cl_appraisal.clinical_appraisals_list,
        name="clinical_literature_appraisal_list",
    ),
    path(
        "<int:id>/clinical_literature_appraisal/<int:appraisal_id>",
        cl_appraisal.clinical_literature_appraisal,
        name="clinical_literature_appraisal",
    ),
    path('api/', include('lit_reviews.api.urls')),
    
    # --------------- full text uplode urls ---------------
    # path("upload_ft", ftviews.upload_ft, name="upload_ft"),
    path("<int:id>/full_text_upload", ftviews.ft_uploader, name="full_text_upload"),
    # path("<int:id>/full_text_clear/<int:article_review_id>/", ftviews.ft_clear, name="full_text_clear"),
    path(
        "<int:id>/ft_download_all_files",
        ftviews.ft_download_all_files,
        name="ft_download_all_files",
    ),
    path("fulltext_upload_help", ftviews.fulltext_upload_help, name="fulltext_upload_help"),
    # path("<int:id>/pdf_highlighter", ftviews.pdf_highlighter, name="pdf_highlighter"),
    

    # --------------- Extraction Fields urls ---------------
    path("<int:id>/extraction_fields", extraction_fields.home, name="extraction_fields"),


    ######################################
    ########## Search Notebook ##########
    ######################################
    # --------------- Search Notebook urls ---------------
    path("search_notebook/", search_notebook_views.home, name="search_notebook"),

]
