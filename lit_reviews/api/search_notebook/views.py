
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status,permissions
from client_portal.models import Project
from lit_reviews.models import (
    LiteratureReview,
    NCBIDatabase,
    LiteratureSearch,
    Client,
    Article,
    ArticleReview,
    ArticleTag,
)
from .serializers import (
    NCBIDatabaseSerializer,
    CreateNewSearchNotebookTermSerializer,
    LiteratureSearchSerializer,
    LiteratureSearchUpdateSerializer,
    UpdateArticleSerializer,
    ArticleReviewSerializer,
)
from lit_reviews.api.home.serializers import LiteratureReviewSerializer
from lit_reviews.api.cutom_permissions import doesClientHaveAccessToProposal
from lit_reviews.api.articles.serializers import ArticleTagSerializer

class SearchNotebookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_or_create_notebook(self, user):
        """
        Retrieve or create the 'Notebook' project and its associated literature review for the given user.
        One note book project should be created per company.
        """
        # project, created = Project.objects.get_or_create(
        #     project_name="Notebook",
        #     client=client,
        #     defaults={"lit_review": LiteratureReview.objects.create(client=client)}
        # )
        # if created:
        #     project.lit_review.save()
        #     project.save()
        # return project.lit_review
        client = user.client 
        if client: 
            literature_review = LiteratureReview.objects.filter(client=client, is_notebook=True).first()
            if literature_review:
                Project.objects.filter(lit_review=literature_review).first()
            else:
                literature_review = LiteratureReview.objects.create(client=client, is_notebook=True)
                Project.objects.create(
                    lit_review=literature_review,
                    project_name="Notebook",
                    client=client,
                )
                protocol = literature_review.searchprotocol
                protocol.max_imported_search_results = 1000
                protocol.save()

            return literature_review

        else:
            literature_review = LiteratureReview.objects.filter(client__is_company=True, is_notebook=True).first()
            if literature_review:
                Project.objects.filter(lit_review=literature_review).first()
            else:
                client = Client.objects.filter(is_company=True).first()
                literature_review = LiteratureReview.objects.create(client=client, is_notebook=True)
                Project.objects.create(
                    lit_review=literature_review,
                    project_name="Notebook",
                    client=client,
                )
                protocol = literature_review.searchprotocol
                protocol.max_imported_search_results = 1000
                protocol.save()

            return literature_review
        

    def get(self, request, *args, **kwargs):
        """
        Retrieve literature searches and databases for the notebook.
        """
        lit_review = self._get_or_create_notebook(request.user)
        lit_review_ser =  LiteratureReviewSerializer(lit_review, context={"request": request})

        # Retrieve literature searches for this notebook
        literature_searches_query = LiteratureSearch.objects.filter(
            literature_review=lit_review
        ).exclude(term__in=["tmp term", "One-Off Manufacturer Search"]).order_by("-id")
        literature_searches = LiteratureSearchSerializer(literature_searches_query, many=True).data

        # Retrieve all NCBI databases
        databases_to_search = NCBIDatabase.objects.filter(
            auto_search_available=True
        ).exclude(
            is_ae=True
        ).exclude(
            is_recall=True
        )
        databases_to_search_serialized = NCBIDatabaseSerializer(databases_to_search, many=True).data

        # load user tags from all available projects
        # if request.user.client:
        #     lit_reviews = LiteratureReview.objects.filter(client=request.user.client)
        # elif request.user.is_ops_member:
        #     lit_reviews = LiteratureReview.objects.filter(client__is_company=False)
        # else:
        #     lit_reviews = LiteratureReview.objects.all()

        lit_reviews = self.request.user.my_reviews()
        tags = ArticleTag.objects.filter(literature_review__id__in=lit_reviews.values("id")).distinct("name")
        tags_ser = ArticleTagSerializer(tags, many=True)
        
        return Response(
            {
                "databases_to_search": databases_to_search_serialized,
                "literature_searches": literature_searches,
                "notebook_review": lit_review_ser.data,
                "tags": tags_ser.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        """
        Add a new literature search term to the notebook.
        """
        lit_review = self._get_or_create_notebook(request.user)

        serializer = CreateNewSearchNotebookTermSerializer(
            data=request.data, context={"user_id": request.user.id, "lit_review_id": lit_review.id}
        )
        serializer.is_valid(raise_exception=True)
        notebook_search = serializer.save()

        return Response({"notebook_search": notebook_search}, status=status.HTTP_200_OK)


class ArticleReviewListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, doesClientHaveAccessToProposal]
    serializer_class = ArticleReviewSerializer

    def get_queryset(self):
        search_ids = self.kwargs.get("search_ids")
        search_ids = search_ids.split(",")
        searches = LiteratureSearch.objects.filter(id__in=search_ids)
        for search in searches:
            self.check_object_permissions(self.request, search)
        queryset = ArticleReview.objects.filter(search__in=searches)

        # tag filter
        article_tag = self.request.query_params.get("tag", None)
        if article_tag:
            article_tags = article_tag.split(",")
            queryset = queryset.filter(tags__name__in=article_tags).distinct()

        # text search filter
        text_filter = self.request.query_params.get("search", None)
        if text_filter:
            queryset = queryset.filter(Q(
                Q(article__title__icontains=text_filter) 
                | Q(article__abstract__icontains=text_filter) 
                | Q(article__citation__icontains=text_filter)    
            )) 

        # Data Base Filter
        db_filter = self.request.query_params.get("db", None)
        if db_filter:
            dbs = db_filter.split(",")
            queryset = queryset.filter(search__db__entrez_enum__in=dbs) 


        # Date Filter
        start_date = self.request.query_params.get("start_date", None)
        if start_date:
            queryset = queryset.filter(search__start_search_interval__gte=start_date) 
        
        end_date = self.request.query_params.get("end_date", None)
        if end_date:
            queryset = queryset.filter(search__end_search_interval__lte=end_date) 

        return queryset.distinct()

class UpdateLiteratureSearchView(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, doesClientHaveAccessToProposal]
    lookup_url_kwarg = "search_id"
    serializer_class = LiteratureSearchUpdateSerializer
    queryset = LiteratureSearch.objects.all()

    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        search = self.get_object()
        serializer = LiteratureSearchSerializer(search)
        return Response(serializer.data , status=status.HTTP_200_OK)
    

class SaveArticleToLibraryView(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, doesClientHaveAccessToProposal]
    lookup_url_kwarg = "article_id"
    serializer_class = UpdateArticleSerializer

    def get_queryset(self):
        request = self.request
        # if request.user.client:
        #     return Article.objects.filter(literature_review__client=request.user.client)
        # if request.user.is_ops_member:
        #     return Article.objects.all()
        # elif request.user.is_superuser or request.user.is_staff:
        #     return Article.objects.all()
        # else:
        #     return Article.objects.none() 
    
        return  Article.objects.filter(literature_review__in=request.user.my_reviews())

    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        article_review_id = request.data.get("article_review_id")
        article_review = ArticleReview.objects.get(id=article_review_id)
        serializer = ArticleReviewSerializer(article_review)
        return Response(serializer.data , status=status.HTTP_200_OK)
    

class BulkSaveArticleToLibraryView(APIView):
    permission_classes = [permissions.IsAuthenticated, doesClientHaveAccessToProposal]
    serializer_class = UpdateArticleSerializer
    
    def post(self, request, *args, **kwargs):
        article_review_ids = request.data.get("article_review_ids")
        is_added_to_library = request.data.get("is_added_to_library", False)
        reviews = ArticleReview.objects.filter(id__in=article_review_ids)
        for review in reviews:
            self.check_object_permissions(request, review.article)
            review.article.is_added_to_library = is_added_to_library
            review.article.save()

        serializer = ArticleReviewSerializer(reviews, many=True)
        return Response(serializer.data , status=status.HTTP_200_OK)