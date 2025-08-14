from django.urls import path

from lit_reviews.api.search_terms import  views as SEARCH_TERMS
from lit_reviews.api.adverse_events import views as AE_VIEWS 
from lit_reviews.api.search_dash import views as SEARCH_DASH
from lit_reviews.api.report_builder import views as REPORT_BUILDER
from lit_reviews.api.keywords import views as KEYWORDS
from lit_reviews.api.extraction_fields import views as EXTRACTIONS
from lit_reviews.api.articles import views as ARTICLES
from lit_reviews.api.tags import views as TAGS
from lit_reviews.api.configs import views as PROJECT_CONFIG
from lit_reviews.api.literature_review import views as LIT_REVIEW
from lit_reviews.api.search_protocol import views as SEARCH_PROTOCOL
from lit_reviews.api.home import views as HOME
from lit_reviews.api.clinical_appraisals import views as CLINICAL_APPRAISALS
from lit_reviews.api.actions import views as ACTIONS
from lit_reviews.api.search_notebook import views as SEARCH_NOTEBOOK
from lit_reviews.api.living_reviews import views as  LIVING_REVIEW

urlpatterns = [

    ######################################
    ############## HOME ##################
    ######################################
    
    path("", HOME.LiteratureReviewListAPIView.as_view(), name="literature_review_list_api"),
    path("analysis/", HOME.LiteratureReviewAnalysisView.as_view(), name="literature_review_analysis_api"),
    path("configs/", HOME.CustomerSettingsAPIView.as_view(), name="customer_settings_api"),
    path("configs/<int:settings_id>/", HOME.UpdateCustomerSettingsAPIView.as_view(), name="update_customer_settings_api"),
    path('<int:id>/prisma-data/', HOME.PrismaANDUserDataAPIView.as_view(), name='prisma_data_api_data'),
    path('custom-label/', HOME.CustomLabelAPIView.as_view(), name='custom_label_api'),
    path("custom-label/<int:custom_label_id>/delete/", HOME.DestroySearchLabelOptionView.as_view(), name="custom_label_option"),
    path('support-tickets/', HOME.SupportTicketCreateAPIView.as_view(), name='support_ticket_create_api'),
     

    ######################################
    ########## ADVERSE EVENTS ############
    ######################################

    path("<int:id>/manual_ae_searches/", AE_VIEWS.ManualAdverEventSearchsView.as_view(), name="manual_ae_searches_api"),
    # DELETE
    path("<int:id>/adverse_events/<int:ae_id>/delete/", AE_VIEWS.DestroyAdverseEventReviewView.as_view(), name="ae_destroy"),
    path("<int:id>/adverse_recalls/<int:ae_id>/delete/", AE_VIEWS.DestroyAdverseRecallReviewView.as_view(), name="recall_destroy"),
    # UPDATE 
    path("<int:id>/adverse_events/<int:ae_id>/update/", AE_VIEWS.UpdateAdverseEventReviewView.as_view(), name="ae_update"),
    path("<int:id>/adverse_recalls/<int:ae_id>/update/", AE_VIEWS.UpdateAdverseRecallReviewView.as_view(), name="recall_update"),

    ######################################
    ############## keywords ###############
    ######################################

    path("<int:id>/keyword_api/", KEYWORDS.KeywordView.as_view(), name="keyword_api"),
    path("<int:id>/keyword_api/<int:custom_kw_id>/delete/", KEYWORDS.CustomKeyword.as_view(), name="custom_kw"),
    
    ######################################
    ######### SEARCH TERMS ###############
    ######################################

    path("<int:id>/search_terms/", SEARCH_TERMS.SearchTermsView.as_view(), name="search_terms_api"),
    path("<int:id>/search_terms/validator/", SEARCH_TERMS.SearchTermValidatorView.as_view(), name="search_terms_validator_api"),
    path("<int:id>/search_terms/update/", SEARCH_TERMS.UpdateSearchTermsView.as_view(), name="search_terms_update_api"),
    path("<int:id>/search_terms/result_summary/", SEARCH_TERMS.ResultSummaryView.as_view(), name="result_summary_api"),
    path("<int:id>/search_terms/delete/<int:prop_id>/", SEARCH_TERMS.DeleteSearchTermsView.as_view(), name="search_terms_delete_api"),
    path("<int:id>/search_terms/preview-results/", SEARCH_TERMS.RunPreviewAutoSearchView.as_view(), name="preview_results_api"),
    path("<int:id>/search_terms/preview-status/", SEARCH_TERMS.CheckPreviewStatusAPI.as_view(), name="preview_status_api"),
    path("<int:id>/search_terms/bulk_delete/", SEARCH_TERMS.BulkSearchTermDelteView.as_view(), name="search_terms_bulk_delete_api"),
    
    ######################################
    ######### SEARCH DASHBOARD ###########
    ######################################

    path("<int:id>/search_dashboard/", SEARCH_DASH.SearechDashboardView.as_view(), name="search_dashboard_api"),
    path("<int:id>/search_dashboard/check_status/", SEARCH_DASH.CheckRunningStatusView.as_view(), name="check_running_status_api"),
    path("<int:id>/search_dashboard/run_auto_search/", SEARCH_DASH.RunAutoSearchView.as_view(), name="run_auto_search_api"),
    path("<int:id>/search_dashboard/exclude_search/", SEARCH_DASH.ExcludeSearchView.as_view(), name="exclude_search_api"),
    path("<int:id>/search_dashboard/clear_database/", SEARCH_DASH.ClearDatabaseView.as_view(), name="clear_database_api"),
    path("<int:id>/search_dashboard/generate_report/", SEARCH_DASH.GenerateSearchReportView.as_view(), name="generate_report_api"),
    path("<int:id>/search_dashboard/validate_manual_file_search_api/", SEARCH_DASH.ValidateManualFileSearchView.as_view(), name="validate_manual_file_search_api"),
    path("<int:id>/search_dashboard/upload_citations/", SEARCH_DASH.UploadOwnCitationsAPIView.as_view(), name="upload_citations_api"),
    path("<int:id>/search_dashboard/request_help/", SEARCH_DASH.RequestSupportHelp.as_view(), name="request_help_api"),
    path("anonymous_request_help/", SEARCH_DASH.AnonymousRequestSupportHelp.as_view(), name="anonymous_request_help_api"),
    path("<int:id>/search_dashboard/generate-s3-url/", SEARCH_DASH.CreateAWSS3DirectUploadURL.as_view(), name="generate_s3_url"),
    
    ######################################
    ########## Report Builder ############
    ######################################

    path("<int:id>/report_builder/", REPORT_BUILDER.ReportBuilderView.as_view(), name="report_builder_api"),   
    path("<int:id>/report_builder/delete/<int:report_id>/", REPORT_BUILDER.DestroyReportAPIView.as_view(), name="delete_report_api"),
    path("<int:id>/report_builder/report_status/", REPORT_BUILDER.ReportStatusAPIView.as_view(), name="report_status_api"),
    path("<int:id>/report_builder/full_text_zip/", REPORT_BUILDER.GenerateFullTextZipView.as_view(), name="full_text_zip_api"),
    path("<int:id>/report_builder/update_config/<int:config_id>/", REPORT_BUILDER.UpdateFinalReportConfigView.as_view(), name="update_config_api"),
    path("<int:id>/report_builder/update_comment/<int:report_id>/", REPORT_BUILDER.UpdateReportCommentView.as_view(), name="update_comment_api"),

    ######################################
    ######### Extraction Fields ##########
    ######################################
    
    path("<int:id>/extraction_fields/", EXTRACTIONS.ExtractionFieldsView.as_view(), name="extraction_fields_api"),
    path("<int:id>/extraction_fields/delete/", EXTRACTIONS.ExtractionFieldsBulkDeleteView.as_view(), name="extraction_fields_delete_api"),
    ######################################
    ############# Articles ###############
    ######################################

    path("<int:id>/articles_list_api/", ARTICLES.ArticlesAPIView.as_view(), name="articles_list_api"),
    path("<int:id>/articles_add_comment_api/", ARTICLES.ArticlesAddCommentAPIView.as_view(), name="articles_add_comment_api"),
    path("<int:id>/articles_comments_api/<int:review_id>/", ARTICLES.ArticlesCommentsListAPIView.as_view(), name="articles_comments_api"),
    path("<int:id>/exclusion_reasons_list_api/", ARTICLES.ExclusionReasonListView.as_view(), name="exclusion_reasons_list_api"),
    path("<int:id>/article_tags_api/", ARTICLES.ArticleTagsListView.as_view(), name="article_tags_api"),
    path("<int:id>/bulk_state_update/", ARTICLES.BulkUpdateArticleStateView.as_view(), name="bulk_state_update"),
    path("<int:id>/article_review_update/<int:review_id>/", ARTICLES.UpdateArticleReviewAPIView.as_view(), name="article_review_update"),
    path("<int:id>/article_review_history/<int:review_id>/", ARTICLES.ArticleReviewHistoryAPIView.as_view(), name="article_review_history"),
    path("<int:id>/article_matches/", ARTICLES.ArticleMatchesAPIView.as_view(), name="article_matches_api"),
    path("<int:id>/attach_pdf_api/", ARTICLES.AttachPdfAPIView.as_view(), name="attach_pdf_api"),
    path("<int:id>/articles-historical-status-api/", ARTICLES.ArticlesHistoricalStateAPI.as_view(), name="articles-historical-status-api"),

    path("<int:id>/duplicates_articles_list_api/", ARTICLES.DuplicateArticlesListView.as_view(), name="duplicates_articles_list_api"),
    path("<int:id>/potential_duplicates_articles_list_api/", ARTICLES.PotentialDuplicateArticlesListView.as_view(), name="potential_duplicates_articles_list_api"),
    path("<int:id>/article_review_update_duplicate/<int:review_id>/", ARTICLES.MarkArticleAsDuplicateView.as_view(), name="article_review_update_duplicate"),
    path("<int:id>/1st-pass-ai-suggestions/", ARTICLES.GenerateAISuggestionsAPI.as_view(), name="1st-pass-ai-suggestions"),
    path("<int:id>/upload-full-text/", ARTICLES.UploadFullTextPDFView.as_view(), name="upload-full-text"),
    path("<int:id>/clear-full-text/", ARTICLES.ClearFullTextAPI.as_view(), name="clear-full-text"),


    ######################################
    ############### Tags #################
    ######################################

    path("<int:id>/tags/", TAGS.ArticleTagListAPIView.as_view(), name="article_tags_list_api"),
    path("<int:id>/tags/<int:tag_id>/delete/", TAGS.ArticleTagDeleteAPIView.as_view(), name="article_tags_delete_api"),
    path("<int:id>/tags/<int:tag_id>/update/", TAGS.ArticleTagUpdateAPIView.as_view(), name="article_tags_update_api"),
    path("<int:id>/tags/create/", TAGS.ArticleTagCreateAPIView.as_view(), name="article_tags_create_api"),
    path("attach-tag-to-articles/", TAGS.AttachTagToArticlesView.as_view(), name="attach-tag-to-articles"),
    
    path("databases/", ARTICLES.DataBasesListAPIView.as_view(), name="databases"),

    ######################################
    ######### Project Config #############
    ######################################
    
    path("<int:id>/project_config_api/", PROJECT_CONFIG.ProjectConfigAPIView.as_view(), name="project_config_api"),
    path("<int:id>/project_config_api/<int:config_id>/update/", PROJECT_CONFIG.UpdateProjectConfigAPIView.as_view(), name="update_project_config_api"),

    ######################################
    ######### Literature Review ##########
    ######################################
    path("create_lit_review/", LIT_REVIEW.CreateLiteratureReviewAPIView.as_view(), name="create_lit_review_api"),
    path("create_device/", LIT_REVIEW.CreateDeviceAPIView.as_view(), name="create_device_api"),
    path("create_client/", LIT_REVIEW.CreateClientAPIView.as_view(), name="create_client_api"),
    path("clients_list/", LIT_REVIEW.ListClientAPIView.as_view(), name="clients_list_api"),
    path("devices_list/", LIT_REVIEW.ListDeviceAPIView.as_view(), name="devices_list_api"),
    path("manufacturer_list/", LIT_REVIEW.ListManufacturerAPIView.as_view(), name="manufacturer_list_api"),
    path("reviews_list/", LIT_REVIEW.LiteratureReviewAPIListView.as_view(), name="reviews_list_api"),
    path("device/<int:device_id>/", LIT_REVIEW.GetDeviceAPIView.as_view(), name="get-devie-api"),

    # living reviews 
    path("create_living_review_api/", LIT_REVIEW.CreateLivingReviewAPIView.as_view(), name="create_living_review_api"),
    path("living-reviews/", LIVING_REVIEW.LivingReviewListAPIView.as_view(), name="living_reviews_list"),
    path("living-review/<int:id>/", LIVING_REVIEW.LivingReviewDetailAPIView.as_view(), name="living_review_detail_api"),
    path("<int:id>/article_reviews/", LIVING_REVIEW.ArticleReviewListAPIView.as_view(), name="article_reviews_list_api"),
    path('living-reviews/<int:id>/update/', LIVING_REVIEW.UpdateLivingReviewAPIView.as_view(), name='update_living_review_api'),
    ######################################
    ######### Search Protocol ############
    ######################################
    path("<int:id>/search_protocol_api/",SEARCH_PROTOCOL.SearchProtocolAPIView.as_view(), name="search_protocol_api"),
    path("<int:id>/search_protocol_api/<int:search_config_id>/",SEARCH_PROTOCOL.UpdateDBSearchConfigurationAPIView.as_view(), name="update_db_search_configuration_api"),

    ######################################
    ####### Clinical Appraisals ##########
    ######################################
    path("<int:id>/clinical-appraisals-list/", CLINICAL_APPRAISALS.ClinicalAppraisalsListAPIView.as_view(), name="clinical-appraisals-list-api"),
    path("<int:id>/appraisals_data/", CLINICAL_APPRAISALS.AppraisalsDataAPIView.as_view(), name="appraisals_data_api"),
    path("<int:id>/clinical_literature_appraisals/upload_citations/", CLINICAL_APPRAISALS.UploadOwnCitationsAPIView.as_view(), name="upload_clinical_appraisals_citations_api"), 
    path("<int:id>/clinical_literature_appraisals/check_status/", CLINICAL_APPRAISALS.CheckRunningCitationView.as_view(), name="check_running_citation_api"),  
    path("<int:id>/clinical_literature_appraisals/import_manual_search/", CLINICAL_APPRAISALS.ImportManualSearchView.as_view(), name="import_manual_search"),  
    path("<int:id>/clinical_literature_appraisals/navigation/", CLINICAL_APPRAISALS.AppraisalNavigationAPIView.as_view(), name="appraisal_navigation_api"),
    path("<int:id>/add_sub_extraction/<int:appraisal_id>/", CLINICAL_APPRAISALS.AddSubExtractionField.as_view(), name="add_sub_extraction_api"),
    path("<int:id>/delete_sub_extraction/<int:appraisal_id>/", CLINICAL_APPRAISALS.DeleteSubExtractionField.as_view(), name="delete_sub_extraction_api"), 
    path("<int:id>/clinical_literature_appraisals/<int:appraisal_id>/", CLINICAL_APPRAISALS.AppraisalDetailAPIView.as_view(), name="appraisal_detail_api"),
    path("<int:id>/clinical_literature_appraisals/<int:appraisal_id>/ai_update/", CLINICAL_APPRAISALS.AppraisalAIUpdateAPIView.as_view(), name='appraisal_ai_update_api'),
    path("<int:id>/appraisals/<int:appraisal_id>/extraction-fields/<int:field_id>/",CLINICAL_APPRAISALS.AppraisalExtractionFieldAPIView.as_view(), name='appraisal_extraction_field_update_api'),
    path("<int:id>/process-all-appraisals/", CLINICAL_APPRAISALS.ProcessClinicalAppraisalAPIView.as_view(), name='process-all-appraisals'),
    path("<int:id>/create-manual-appraisal/", CLINICAL_APPRAISALS.CreateManualAppraisalAPI.as_view(), name="create-manual-appraisal-api"),    
    path("<int:id>/pdf-highlighting/", CLINICAL_APPRAISALS.PDFHighlightingAPIView.as_view(), name="pdf-highlighting-api"),


    ######################################
    ############## Actions ###############
    ######################################

    path("<int:id>/actions_api/", ACTIONS.ActionsView.as_view(), name="actions_api"),
    path("<int:id>/actions_filters_api/", ACTIONS.ActionsFiltersView.as_view(), name="actions_filters_api"),

    ######################################
    ############## Search Notebook ###############
    ######################################

    path("search_notebook_api/", SEARCH_NOTEBOOK.SearchNotebookAPIView.as_view(), name="search_notebook_api"),
    path("update_notebook_seaerch_api/<int:search_id>/", SEARCH_NOTEBOOK.UpdateLiteratureSearchView.as_view(), name="update_note_booksearch_search"),
    path("save_to_library_api/<int:article_id>/", SEARCH_NOTEBOOK.SaveArticleToLibraryView.as_view(), name="save_to_library_api"),
    path("bulk_save_to_library_api/", SEARCH_NOTEBOOK.BulkSaveArticleToLibraryView.as_view(), name="bulk_save_to_library_api"),
    path("search_results_api/<str:search_ids>/", SEARCH_NOTEBOOK.ArticleReviewListAPIView.as_view(), name="search_results_api"),
]
