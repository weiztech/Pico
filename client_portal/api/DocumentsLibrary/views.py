from django.db.models import Q
from django.core.files import File as DjangoFile

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.paginator import Paginator
import math
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import UpdateAPIView 
import zipfile
import uuid

from backend.logger import logger
from lit_reviews.models import (
    Article,
    Device,
    Article,
    LiteratureReview,
    LiteratureSearch,
    ArticleTag,
)
from lit_reviews.api.articles.serializers import ArticleTagSerializer
from lit_reviews.api.search_dash.serializers import UploadOwnCitationsSerializer
from client_portal.models import (
    Project,
)
from client_portal.api.DocumentsLibrary.serializers import (
    CitationSerializer,
    DeviceSerializer,
    LiteratureReviewSerializer,
    UpdateArticleSerializer,
    ProjectSerializer,
)
from client_portal.api.permissions import isArticleOwner

class UpdateArticleView(UpdateAPIView):
    queryset = Article.objects.all()
    permission_classes = [isArticleOwner]
    serializer_class = UpdateArticleSerializer
    lookup_url_kwarg = "article_id"
    parser_classes = (MultiPartParser, FormParser,)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        article = self.get_object()
        serializer = CitationSerializer(article, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class DocumentsLibraryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):        
        page_number = int(self.request.query_params.get('page_number', 1))
        text_filter = request.query_params.get('search_term', None)
        page_size = self.request.query_params.get('page_size', 50)
        device_filter = self.request.query_params.get('device_filter', None)
        lit_review_filter = self.request.query_params.get('lit_review_filter', None)
        year_filter = self.request.query_params.get('year_filter', None)
        db_filter = self.request.query_params.get("db", None)
        lit_reviews = request.user.my_reviews()
                    
        __filters = {}
        
        if year_filter:
            logger.debug(f"year filter: {year_filter}")
            __filters["publication_year__icontains"] = year_filter

        if device_filter:
            logger.debug(f"device filter: {device_filter}")
            __filters["reviews__search__literature_review__device__id"] = device_filter

        if lit_review_filter:
            logger.debug(f"lit review filter: {lit_review_filter}")
            __filters["reviews__search__literature_review__id"] = lit_review_filter

        # Data Base Filter
        if db_filter:
            dbs = db_filter.split(",")
            logger.debug(f"database filter: {lit_review_filter}")
            __filters["reviews__search__db__entrez_enum__in"] = dbs

        belong_to_user_reviews = Q(reviews__search__literature_review__in=lit_reviews) | Q(literature_review__in=lit_reviews)
        non_notebook_reviews = Q(reviews__search__literature_review__is_notebook=False) | Q(literature_review__is_notebook=False) | Q(is_added_to_library=True) 

        entries = Article.objects.filter(
            Q(belong_to_user_reviews & Q(non_notebook_reviews))
        ).distinct("article_unique_id")
        entries = entries.filter(**__filters)
        
        if text_filter:
            entries = entries.filter(
                Q (
                    Q(title__icontains=text_filter) 
                    | 
                    Q(citation__icontains=text_filter)
                )
            )
        
        paginator = Paginator(entries , page_size)
        serializer = CitationSerializer(paginator.page(page_number) , many=True, context={'request':request})
        last_page_number = int(math.floor(paginator.count / page_size)) + 1

        return Response({
            "entries": serializer.data,
            "count": paginator.count,
            "page_number": page_number,
            "last_page_number": last_page_number,
        }, status=status.HTTP_200_OK)


class LibraryEntryFiltersAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):        

        # if request.user.client:
        #     projects = Project.objects.filter(client=request.user.client)
        # elif request.user.is_ops_member:
        #     projects = Project.objects.filter(client__is_company=False)
        # else:
        #     projects = Project.objects.all()
        
        projects = Project.objects.filter(lit_review__in=request.user.my_reviews())
        projects_ser = ProjectSerializer(projects, many=True)

        # if request.user.client:
        #     lit_reviews = LiteratureReview.objects.filter(client=request.user.client)
        # elif request.user.is_ops_member:
        #     lit_reviews = LiteratureReview.objects.filter(client__is_company=False)
        # else:
        #     lit_reviews = LiteratureReview.objects.all()
        lit_reviews = request.user.my_reviews()

        lit_reviews_ser = LiteratureReviewSerializer(lit_reviews, many=True)

        devices = Device.objects.filter(id__in=lit_reviews.values("device__id"))
        devices_ser = DeviceSerializer(devices, many=True)

        tags = ArticleTag.objects.filter(literature_review__id__in=lit_reviews.values("id")).distinct("name")
        tags_ser = ArticleTagSerializer(tags, many=True)

        return Response({
            "devices": devices_ser.data,
            "projects": projects_ser.data,
            "tags": tags_ser.data,
            "lit_reviews": lit_reviews_ser.data,
        }, status=status.HTTP_200_OK)
    

class CreateArticleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated,]
    
    def post(self, request, *args, **kwargs):
        article_data = request.data
        title = article_data['title']
        abstract = article_data['abstract']
        citation = article_data['citation']
        pmc_uid = article_data['pmc_uid']
        pubmed_uid = article_data['pubmed_uid']
        pdf_file = article_data['pdf_file']
        project_id = article_data['project']
        zip_file = article_data['zip_file']
        type_creation = article_data['type_creation']
        pub_date = article_data['pub_date']

        project = Project.objects.filter(id=project_id).first()

        if type_creation == "single":
            # creation single article
            article_check_pubmed_uid = Article.objects.filter(
                pubmed_uid=pubmed_uid
            ).first()
            article_check_pmc_uid = Article.objects.filter(
                pmc_uid=pmc_uid
            ).first()

            if article_check_pubmed_uid:
                article = article_check_pubmed_uid
                return Response(status=status.HTTP_400_BAD_REQUEST,data={"Pubmed UID":"Article Already Exist"})
            elif article_check_pmc_uid:
                article = article_check_pmc_uid
                return Response(status=status.HTTP_400_BAD_REQUEST,data={"Pubmed UID":"Article Already Exist"})
            else:
                lit_searches = LiteratureSearch.objects.filter(literature_review__in=request.user.my_reviews()) 

                if lit_searches.count() < 1:
                    return Response(status=status.HTTP_400_BAD_REQUEST,data={"Device":"You have no projects, creating articles requires a project to be attached to, please contact support for help!"})

                
                article = Article.objects.create(
                    title=title,
                    abstract=abstract,
                    citation=citation,
                    pmc_uid=pmc_uid,
                    pubmed_uid=pubmed_uid,
                    full_text=pdf_file,
                    literature_review=project.lit_review,
                    is_added_to_library=True,
                    publication_year=pub_date,
                )

                serializer = CitationSerializer(article, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif type_creation == "":
            serializer = UploadOwnCitationsSerializer(data=request.data, context={"request": request, "literature_review": project.lit_review})
            serializer.is_valid(raise_exception=True)
            results = serializer.save()
            return Response(results, status=status.HTTP_200_OK)
    
        else:            
            if zipfile.is_zipfile(zip_file):
                with zipfile.ZipFile(zip_file, mode="r") as archive:
                    for pdf in archive.infolist():
                        # Read contents of the file
                        file_name = pdf.filename.split("/")[1]
                        file_content = archive.open(pdf)
                        full_text_file = DjangoFile(file_content, name=file_name)

                        if file_name:
                            logger.debug(f"Full text file found : {file_name}")
                            article = Article.objects.create(
                                title="No title provided yet",
                                abstract="No abstract provided yet",
                                citation="No citation provided yet",
                                pmc_uid=uuid.uuid4().hex,
                                pubmed_uid=uuid.uuid4().hex,
                                full_text= full_text_file
                            )

                            # library_entry = article.library_entry
                            # library_entry.projects.add(project)

                return Response(status=status.HTTP_200_OK)

            else:
                error_msg = "the file you are trying to upload is not a zip, Please upload a zip file!"
                return Response(status=status.HTTP_400_BAD_REQUEST,data={"Zip file": error_msg})

