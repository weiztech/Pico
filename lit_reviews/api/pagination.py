from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 50  # Number of items per page
    page_size_query_param = 'page_size'  # Query parameter to override the default page size
    max_page_size = 100  # Maximum number of items per page

class CustomPaginationActions(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'  # Query parameter to override the default page size
    max_page_size = 100  # Maximum number of items per page