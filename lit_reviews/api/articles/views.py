from fuzzywuzzy import fuzz

from rest_framework.views import APIView
from rest_framework import serializers 
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView, RetrieveAPIView
from rest_framework import permissions, response, status, filters
from django.db.models import Q, Max, Min
from django.shortcuts import get_object_or_404 
from rest_framework.response import Response
from backend.logger import logger
from lit_reviews.api.pagination import CustomPagination
from lit_reviews.models import (
    ArticleReview, 
    LiteratureReview, 
    ExclusionReason,
    NCBIDatabase,
    ArticleTag,
    Comment,
    Article,
    DuplicatesGroup,
)
from .serializers import (
    ArticleReviewSerializer, 
    ExclusionReasonSerializer,
    ArticleReviewUpdateSerializer,
    NCBIDatabaseSerializer,
    ArticleTagSerializer,
    CommentSerializer,
    CreateCommentSerializer,
    ArticleSerializer,
    DuplicatesGroupSerializer,
    UploadFullTextSerializer,
    FullTextUploaderArticleReviewSerializer,
    ClearFullTextSerializer,
    ArticleReviewHistoricalStatusResponseSerializer,
    ArticleReviewHistoricalStatusRequestSerializer,
)
from lit_reviews.api.cutom_permissions import (
    isProjectOwner, 
    IsNotArchived, 
    DoesUserHaveEnoughCredits, 
    DoesUserHaveEnoughCreditsObjectPermission,
)
from lit_reviews.tasks import bulk_article_review_update_async, generate_ai_suggestionss_first_pass_async
from lit_reviews.helpers.articles import calculate_full_text_status


class ArticlesAddCommentAPIView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    serializer_class = CreateCommentSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=request.user)

        # Sending email notification to project related users upon comment creation not needed as for now 16/07/2024
        # lit_review_id = self.kwargs.get("id")
        # domain_name = request.build_absolute_uri('/')
        # send_email_when_comment_created.delay(lit_review_id, instance.id, domain_name)
        
        serializer = CommentSerializer(instance=instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ArticlesCommentsListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            article_review=self.kwargs['review_id']
        )
    

class ArticlesHistoricalStateAPI(APIView):
    """
    Given a list of article id's return back historical status (article review state in the recent project) 
    for each article review.
    """
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def post(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        context = {"request": request, "literature_review": lit_review}
        serializer = ArticleReviewHistoricalStatusRequestSerializer(data=request.data, many=True, context=context)
        serializer.is_valid(raise_exception=True)
        articles = serializer.save()
        resp_serializer = ArticleReviewHistoricalStatusResponseSerializer(articles, many=True, context=context)
        return Response(resp_serializer.data, status=status.HTTP_200_OK) 
    

class ArticlesAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ArticleReviewSerializer
    pagination_class = CustomPagination
    queryset = ArticleReview.objects.all()
    # Explicitly specify which fields the API may be ordered against
    ordering_fields = ('article__title', '-article__title', 'score', "-score", "id", "-id")
    # This will be used as the default ordering
    ordering = ('-article__title')
    filter_backends = (filters.OrderingFilter,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        queryset = queryset.filter(search__literature_review=lit_review) 

        # Calculate max_score and min_score
        self.max_score = queryset.aggregate(max_score=Max('score'))['max_score']
        self.min_score = queryset.aggregate(min_score=Min('score'))['min_score']

        # state filter
        article_state = self.request.query_params.get("state", None)
        if article_state:
            article_states = article_state.split(",")
            queryset = queryset.filter(state__in=article_states) 
        
        # tag filter
        article_tag = self.request.query_params.get("tag", None)
        if article_tag:
            article_tags = article_tag.split(",")
            queryset = queryset.filter(tags__name__in=article_tags).distinct()

        # score filter
        max_score_filter = self.request.query_params.get("max_score", None)
        min_score_filter = self.request.query_params.get("min_score", None)

        if max_score_filter:
            queryset = queryset.filter(score__lte=max_score_filter) 
        if min_score_filter:
            queryset = queryset.filter(score__gte=min_score_filter) 

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
        
        return queryset
        
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            paginated_response.data['max_score'] = self.max_score
            paginated_response.data['min_score'] = self.min_score
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        response_data['max_score'] = self.max_score
        response_data['min_score'] = self.min_score
        return response.Response(response_data)

class ExclusionReasonListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ExclusionReasonSerializer

    def get_queryset(self):
        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return ExclusionReason.objects.filter(literature_review=lit_review) 
    
class ArticleTagsListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ArticleTagSerializer

    def get_queryset(self):
        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return ArticleTag.objects.filter(literature_review=lit_review) 
    
class DataBasesListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = NCBIDatabaseSerializer
    queryset = NCBIDatabase.objects.filter(is_archived=False) 

class BulkUpdateArticleStateView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived, DoesUserHaveEnoughCredits]
    
    def post(self, request, *args, **kwargs):
        is_check = request.data.get("is_check", None)
        lit_review_id = self.kwargs.get("id")
        reviews_ids = request.data.get("review_ids", [])
        if is_check:
            article_reviews = ArticleReview.objects.filter(id__in=reviews_ids, search__literature_review__id=lit_review_id)
            serializer = ArticleReviewSerializer(article_reviews, many=True, context={"request": request})
            return response.Response({"success": True, "updated_articles": serializer.data}, status=status.HTTP_200_OK)
        
        state = request.data.get("state", None)
        note = request.data.get("notes", None)
        exclusion_reason = request.data.get("exclusion_reason", None)
        exclusion_comment = request.data.get("exclusion_comment", None)
        tag_id = request.data.get("tag", None)
        if request.data.get("tags", None):
            tag_ids = request.data.get("tags", None)
        else:
            tag_ids = [tag_id]
        
        if state == "E" and not exclusion_reason:
            raise serializers.ValidationError({"Exclusion Reason": "if you wish to exclude articles, you have to provide and Exclusion Reason!"})
        bulk_article_review_update_async(lit_review_id, reviews_ids, state, note, exclusion_reason, exclusion_comment, tag_ids, request.user.id)
        article_reviews = ArticleReview.objects.filter(id__in=reviews_ids, search__literature_review__id=lit_review_id)
        serializer = ArticleReviewSerializer(article_reviews, many=True, context={"request": request})
        return response.Response({"success": True, "updated_reviews": serializer.data}, status=status.HTTP_200_OK)
    

class UpdateArticleReviewAPIView(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived, DoesUserHaveEnoughCreditsObjectPermission]
    serializer_class = ArticleReviewUpdateSerializer
    lookup_url_kwarg = "review_id" 

    def get_queryset(self):
        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return ArticleReview.objects.filter(search__literature_review=lit_review) 
    
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = get_object_or_404(ArticleReview, id=kwargs.get("review_id"))
        serializer = ArticleReviewSerializer(instance, context={"request": request})
        data = serializer.data
        hist_serializer = ArticleReviewHistoricalStatusResponseSerializer(instance, context={"request": request})
        data["previous_article_state"] = hist_serializer.data.get("previous_article_state")
        return response.Response(data)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request 
        return context 
    
class ArticleReviewHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    lookup_url_kwarg = "review_id" 
    
    def get(self, request, *args, **kwargs):
        review_id = kwargs.get("review_id")
        review = get_object_or_404(ArticleReview, pk=review_id)

        if review.article.pmc_uid:
            reviews_history = ArticleReview.objects.filter(article__pmc_uid=review.article.pmc_uid).exclude(id=review.id).order_by("-search__created_time")
        elif review.article.pubmed_uid:
            reviews_history = ArticleReview.objects.filter(article__pubmed_uid= review.article.pubmed_uid).exclude(id=review.id).order_by("-search__created_time")
        else:
            reviews_history = ArticleReview.objects.filter(article= review.article).exclude(id=review.id).order_by("-search__created_time")


        reviews_history = reviews_history.filter(search__literature_review__in=request.user.my_reviews())
        serializer = ArticleReviewSerializer(reviews_history, many=True, context={"request": request})
        return response.Response(serializer.data)
    

class ArticleMatchesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsNotArchived]
    
    def post(self, request, *args, **kwargs):

        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        article_id = request.data.get("article_id", None)
        match_method = request.data.get("match_method", None)

        if not article_id or not match_method:
            return Response(
                {"detail": "Both 'article_id' and 'match_method' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the article based on article_id
        try:
            our_article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response(
                {"detail": f"Article with id {article_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if match_method == 'by_id':
            # Initialize an empty Q object
            query = Q()

            # Add conditions only if the fields are not empty or None
            if our_article.pmc_uid:
                query |= Q(pmc_uid=our_article.pmc_uid)
            if our_article.pubmed_uid:
                query |= Q(pubmed_uid=our_article.pubmed_uid)
            if our_article.doi:
                query |= Q(doi=our_article.doi)

            # If query is not empty, proceed to filter, else return no matches
            if query:
                articles_matches = Article.objects.filter(query).exclude(id=our_article.id)
                # Filter out articles where full_text does not exist (is None or empty)
                articles_matches = articles_matches.exclude(full_text__isnull=True).exclude(full_text__exact='')
            else:
                articles_matches = Article.objects.none()  # No valid fields to filter by

        elif match_method == 'by_title':
            articles_matches = []
            all_articles = Article.objects.all().exclude(id=our_article.id).exclude(full_text__isnull=True).exclude(full_text__exact='')
            for article in all_articles:
                citation_fuzzy = fuzz.token_set_ratio(our_article.citation, article.citation)
                abstract_fuzzy =  fuzz.token_set_ratio(our_article.abstract, article.abstract)
                title_fuzzy = fuzz.token_set_ratio(our_article.title, article.title)

                # ## to look for the default 'no citaiton found or abstract text' 
                if article.abstract.strip().lower().find("citemed") != -1:
                    abstract_fuzzy = 0

                if citation_fuzzy > 70 and abstract_fuzzy > 90 and title_fuzzy > 95:
                    articles_matches.append(article)

        else:
            return Response(
                {"detail": "Invalid 'match_method'. Must be 'by_id' or 'by_title'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serialize the matched articles
        serializer = ArticleSerializer(articles_matches, many=True, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class AttachPdfAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsNotArchived]

    def post(self, request, *args, **kwargs):

        article_id = request.data.get('article_id')
        current_article_id = request.data.get('current_article_id')
        # Fetch the articles
        article = get_object_or_404(Article, pk=article_id)
        current_article = get_object_or_404(Article, pk=current_article_id)

        # Assign the full_text (PDF) from the selected article to the current article
        current_article.full_text = article.full_text
        current_article.save()

        return Response({"message": "PDF attached successfully."}, status=status.HTTP_200_OK)
    

class DuplicateArticlesListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = DuplicatesGroupSerializer
    pagination_class = CustomPagination
    queryset = DuplicatesGroup.objects.all()
    # Explicitly specify which fields the API may be ordered against
    ordering_fields = ('original_article_review__article__title', '-original_article_review__article__title', "original_article_review__id", "-original_article_review__id")
    # This will be used as the default ordering
    ordering = ('-original_article_review__article__title')
    filter_backends = (filters.OrderingFilter,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        queryset = queryset.filter(
            original_article_review__search__literature_review=lit_review
        ) 

        # state filter
        original_article_review_state = self.request.query_params.get("state", None)
        if original_article_review_state:
            original_article_review_states = original_article_review_state.split(",")
            queryset = queryset.filter(original_article_review__state__in=original_article_review_states) 

        # text search filter
        text_filter = self.request.query_params.get("search", None)
        if text_filter:
            queryset = queryset.filter(Q(
                Q(original_article_review__article__title__icontains=text_filter) 
                | Q(original_article_review__article__abstract__icontains=text_filter) 
                | Q(original_article_review__article__citation__icontains=text_filter)    
            )) 

        # Data Base Filter
        db_filter = self.request.query_params.get("db", None)
        if db_filter:
            dbs = db_filter.split(",")
            queryset = queryset.filter(original_article_review__search__db__entrez_enum__in=dbs) 
        
        return queryset
        
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data

        return response.Response(response_data)
    
    

class PotentialDuplicateArticlesListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ArticleReviewSerializer
    pagination_class = CustomPagination
    queryset = ArticleReview.objects.all()
    # Explicitly specify which fields the API may be ordered against
    ordering_fields = ('article__title', '-article__title', 'score', "-score", "id", "-id")
    # This will be used as the default ordering
    ordering = ('-article__title')
    filter_backends = (filters.OrderingFilter,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        duplicate_or_original_duplicate = Q(
            Q(state='D')
            |
            Q(potential_duplicate_for__state="D")
        )
        queryset = queryset.filter(search__literature_review=lit_review, potential_duplicate_for__isnull=False).exclude(duplicate_or_original_duplicate)

        # state filter
        article_state = self.request.query_params.get("state", None)
        if article_state:
            article_states = article_state.split(",")
            queryset = queryset.filter(state__in=article_states) 
        

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
        
        return queryset
        
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        return response.Response(response_data)


class MarkArticleAsDuplicateView(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ArticleReviewUpdateSerializer
    lookup_url_kwarg = "review_id" 

    def get_queryset(self):
        lit_review_id = self.kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return ArticleReview.objects.filter(search__literature_review=lit_review) 
    
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = get_object_or_404(ArticleReview, id=kwargs.get("review_id"))
        # we just need to do 
        instance.state = "D"

        if instance.potential_duplicate_for:
            try:
                duplicates_group, created = DuplicatesGroup.objects.get_or_create(original_article_review=instance.potential_duplicate_for)
            except:
                duplicates_group = DuplicatesGroup.objects.filter(original_article_review=instance.potential_duplicate_for).first()
            # Add the current article review as a duplicate
            duplicates_group.duplicates.add(instance)
        
        instance.save()

        serializer = ArticleReviewSerializer(instance, context={"request": request})
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class GenerateAISuggestionsAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def post(self, request, *args, **kwargs):
        lit_review_id = self.kwargs.get("id")
        sorting = self.request.query_params.get("sorting", "id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        article_reviews = ArticleReview.objects.filter(
            search__literature_review=lit_review
        ).order_by(sorting).values_list("id", flat=True)
        article_reviews = list(article_reviews)
        generate_ai_suggestionss_first_pass_async.delay(article_reviews, sorting)

        return response.Response("", status=status.HTTP_200_OK)
    

class UploadFullTextPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        sorting = request.query_params.get('sorting', "full_text_status")
        article_reviews = ArticleReview.objects.filter(
            search__literature_review_id=lit_review_id, state="I"
        ).prefetch_related("article")
        article_reviews = calculate_full_text_status(article_reviews)
        article_reviews = article_reviews.order_by(sorting)
        serializer = FullTextUploaderArticleReviewSerializer(article_reviews, many=True)

        return response.Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        serializer_context = {"literature_review": lit_review, "request": request}
        serializer = UploadFullTextSerializer(data=request.data, context=serializer_context)
        serializer.is_valid(raise_exception=True)
        article_review = serializer.save()

        response_serializer = FullTextUploaderArticleReviewSerializer(article_review)
        return response.Response(response_serializer.data, status=status.HTTP_200_OK)


class ClearFullTextAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    
    def post(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        serializer_context = {"literature_review": lit_review, "request": request}
        serializer = ClearFullTextSerializer(data=request.data, context=serializer_context)
        serializer.is_valid(raise_exception=True)
        article_review = serializer.save()

        response_serializer = FullTextUploaderArticleReviewSerializer(article_review)
        return response.Response(response_serializer.data, status=status.HTTP_200_OK)
  

# class ArticleReviewDetailsAPI(RetrieveAPIView):
#     permission_classes = [permissions.IsAuthenticated, isProjectOwner]
#     queryset = ArticleReview.objects.all()
#     serializer_class = ArticleReviewSerializer
#     lookup_url_kwarg = "article_id"

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         literature_review_id = self.kwargs.get("id")
#         queryset = queryset.filter(search__literature_review__id=literature_review_id)
#         return queryset