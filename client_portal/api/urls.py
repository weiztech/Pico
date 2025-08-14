from django.urls import path
from client_portal.api.DocumentsLibrary import views as DocuumentsLibraryViews 
from client_portal.api.projects import views as ProjectsViews 
from client_portal.api.AutomatedSearch import views as AutomatedSearchViews 

urlpatterns = [

    ######################################
    ############## Projects #############
    ######################################
    path("projects/", ProjectsViews.ProjectsListAPIView.as_view(), name="projects_api"),
    path("devices/", ProjectsViews.DeviceListAPIView.as_view(), name="devices_api"),
    path("messages/", ProjectsViews.MessagesListAPIView.as_view(), name="messages_api"),

    ######################################
    ########## Documents Lib #############
    ######################################
    path("documents_library/", DocuumentsLibraryViews.DocumentsLibraryAPIView.as_view(), name="documents_library_api"),
    path("library_entry_filters/", DocuumentsLibraryViews.LibraryEntryFiltersAPI.as_view(), name="library_entry_filters"),
    path("update_article/<int:article_id>/", DocuumentsLibraryViews.UpdateArticleView.as_view(), name="update_article_api"),
    path("documents_library/create_article", DocuumentsLibraryViews.CreateArticleAPIView.as_view(), name="create_article_api"),
    
   
    ######################################
    ########## Automated Search ##########
    ######################################

    path("automated_search/", AutomatedSearchViews.AutomatedSearchAPIView.as_view(), name="automated_search_api"),
    path("create_automated_search/", AutomatedSearchViews.CreateAutomatedSearchAPIView.as_view(), name="create_automated_search_api"),
    path("automated_search_results/<int:search_id>/", AutomatedSearchViews.AutomatedSearchResultsAPIView.as_view(), name="automated_search_results_api"),
    path("automated_search_save_to_library/<int:search_id>/", AutomatedSearchViews.AutomatedSearchSaveToLibraryAPIView.as_view(), name="automated_search_save_to_library_api"),
    path("create_article_comment_api/", AutomatedSearchViews.CreateArticleCommentAPIView.as_view(), name="create_article_comment_api"),
    path("update_automated_search_api/<int:search_id>/", AutomatedSearchViews.UpdateAutomatedSearchAPIView.as_view(), name="update_automated_search_api"),
     
]