from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
import json
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from client_portal.tasks import create_terms_for_automated_searches_initial
from client_portal.models import (
    AutomatedSearchProject,
    ArticleComment,
    LibraryEntry,
)
from lit_reviews.models import (
    Device,
    Manufacturer,
    NCBIDatabase,
    LiteratureReview,
    Article,
    LiteratureSearch,
    LiteratureReviewSearchProposal,
    ArticleReview,
    Client,
)

from client_portal.api.AutomatedSearch.serializers import (
    AutomatedSearchProjectSerializer,
    DeviceSerializer,
    ManufacturerSerializer,
    NCBIDatabaseSerializer,
    ArticleSerializer,
    DateRangesFilterValuesSerailizer,
    ArticleReviewSerializer,
    ClientSerailizer,
)



from client_portal.api.permissions import isClient, isArticleOwner


class AutomatedSearchAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):    
        if request.user.client:    
            automated_search_projects = AutomatedSearchProject.objects.filter(client=request.user.client).order_by("-id")
        else:
            automated_search_projects = AutomatedSearchProject.objects.all().order_by("-id")

        serializer = AutomatedSearchProjectSerializer(automated_search_projects,many=True)
        return Response({
            "entries": serializer.data,
        }, status=status.HTTP_200_OK)


class CreateAutomatedSearchAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):   
        if request.user.client:  
            lit_reviews = LiteratureReview.objects.filter(client=request.user.client)
            clients_list = []
        else:
            lit_reviews = LiteratureReview.objects.all()
            clients = Client.objects.all()
            clients_ser = ClientSerailizer(clients, many=True)
            clients_list = clients_ser.data
            
        devices = Device.objects.filter(literaturereview__in=lit_reviews).distinct()
        devices_ser = DeviceSerializer(devices, many=True)

        manufacturers = Manufacturer.objects.filter(device__in=devices).distinct()
        manufacturers_ser = ManufacturerSerializer(manufacturers, many=True)

        not_isrecall = Q( Q(is_recall=None) | Q(is_recall=False) )
        not_isae = Q( Q(is_ae=None) | Q(is_ae=False) )
        not_recall_and_not_ae = Q( not_isrecall & not_isae)
        isrecall_or_isae = Q( Q(is_ae=True) | Q(is_recall=True) )


        lit_dbs = NCBIDatabase.objects.filter(not_recall_and_not_ae, is_archived=False)
        
        ae_databases = NCBIDatabase.objects.filter(isrecall_or_isae, is_archived=False)
        ae_basic_dbs = []
        ae_extra_dbs = []
        
        for ae_database in ae_databases:
            if ae_database.entrez_enum == "maude_recalls" or ae_database.entrez_enum == "embase" or ae_database.entrez_enum == "scholar":
                ae_basic_dbs.append(ae_database)
            else:
                ae_extra_dbs.append(ae_database)


        lit_dbs_ser = NCBIDatabaseSerializer(lit_dbs, many=True)
        ae_basic_dbs_ser = NCBIDatabaseSerializer(ae_basic_dbs, many=True)
        ae_extra_dbs_ser = NCBIDatabaseSerializer(ae_extra_dbs, many=True)


        return Response({
                "devices": devices_ser.data,
                "manufacturers": manufacturers_ser.data,
                "lit_dbs": lit_dbs_ser.data,
                "ae_basic_dbs": ae_basic_dbs_ser.data,
                "ae_extra_dbs": ae_extra_dbs_ser.data,
                "clients": clients_list,
            }, 
            status=status.HTTP_200_OK
        )
    
    def post(self, request, *args, **kwargs):
        # Extract data from the POST request
        automation_data = request.data

        create_device = automation_data["createDevice"]
        create_manufacturer = automation_data["createManufacturer"]
        device_name = automation_data["deviceName"]
        manufacturer_name = automation_data["manufacturerName"]
        manufacturer = automation_data["selectedManufacturer"]
        classification = automation_data["classification"]
        markets = automation_data["markets"]
        selected_device = automation_data["selectedDevice"]
        selected_interval = automation_data["selectedInterval"]
        selected_dbs_json = request.POST.get('selectedDbs')
        selected_dbs = json.loads(selected_dbs_json)
        search_type = automation_data["searchType"]
        search_term = automation_data["searchTerms"]
        search_file = automation_data["searchFile"]
        start_date = automation_data["startDate"]
        selected_client = automation_data["client"]

        if create_device == "true":
            # Your logic for creating a device
            if create_manufacturer == "true":
                manufacturer = Manufacturer.objects.create(name=manufacturer_name)
                manufacturer.save()
            else:
                manufacturer = get_object_or_404(Manufacturer, name=manufacturer)

            device = Device.objects.create(
                name = device_name,
                manufacturer = manufacturer,
                classification=classification,
                markets=markets
            )
            device.save()
        else:
            device = Device.objects.filter(id = selected_device).first()

        if request.user.client:
            client = request.user.client
        else:
            client = get_object_or_404(Client, id=selected_client)

        # create lit_review
        __filters = {
            "client": client,
            "device": device,
            "is_autosearch": True,
        }
        lit_review = LiteratureReview.objects.filter(**__filters).first()
        if not lit_review:
            lit_review = LiteratureReview.objects.create(**__filters)
            lit_review.save()
            lit_review.authorized_users.add(request.user)

        automated_search_project = AutomatedSearchProject.objects.create(
            lit_review = lit_review,
            client = client,
            interval = selected_interval,
            start_date = start_date,
        )
        automated_search_project.save()

        if search_type == 'terms':
            automated_search_project.terms = search_term
            create_terms_for_automated_searches_initial.delay(
                selected_dbs, 
                search_term, 
                lit_review.id, 
                start_date, 
                selected_interval, 
                str(automated_search_project.client),
                automated_search_project.id,
            )

        else:
            automated_search_project.terms_file = search_file
        automated_search_project.save()


        for db in selected_dbs:
            db_item = NCBIDatabase.objects.filter(displayed_name = db).first()
            automated_search_project.databases_to_search.add(db_item)
            protocol = lit_review.searchprotocol
            if db_item.is_ae or db_item.is_recall:
                protocol.ae_databases_to_search.add(db_item)
            else:
                protocol.lit_searches_databases_to_search.add(db_item)
            
            protocol.lit_date_of_search = start_date
            protocol.ae_date_of_search = start_date
            protocol.save()

        return Response({
            "message": "Automated Search Project Created Successfully"
        }, status=status.HTTP_200_OK)
        



class AutomatedSearchResultsAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):        
        search_id = self.kwargs.get('search_id')
        date_filter = self.request.query_params.get("date_filter")
        automated_search = AutomatedSearchProject.objects.filter(id = search_id).first()

        article_reviews = ArticleReview.objects.filter(
            search__literature_review=automated_search.lit_review,
            search__term=automated_search.terms,
        ).exclude(state="D")
        lit_searches = LiteratureSearch.objects.filter(
            literature_review=automated_search.lit_review,
            term=automated_search.terms,
        )
        
        completed_searches = [search for search in lit_searches if search.is_completed] 
        did_search_fail = lit_searches.filter(import_status="INCOMPLETE-ERROR").count() > 0
        is_search_completed =  len(completed_searches) == lit_searches.count()
        
        search_status = "Pending" 
        if did_search_fail: 
            search_status = "Failed"
        elif is_search_completed:
            search_status = "Completed"

        ranges_dates_distinct = lit_searches.distinct("start_search_interval").values(
            "start_search_interval", "end_search_interval"
        )
        ranges_dates_distinct = [
            {
                "id": date["start_search_interval"].strftime("%d-%m-%Y"), 
                "value": "{} to {}".format(
                    date["start_search_interval"].strftime("%d-%m-%Y"), 
                    date["end_search_interval"].strftime("%d-%m-%Y")
                )
            } 
            for date in ranges_dates_distinct
        ]
        dates_filter_values_ser = DateRangesFilterValuesSerailizer(ranges_dates_distinct, many=True)

        if date_filter:
            date_filter = timezone.datetime.strptime(date_filter, "%d-%m-%Y")
            article_reviews = article_reviews.filter(search__start_search_interval=date_filter)
            lit_searches = lit_searches.filter(start_search_interval=date_filter)
            
            completed_searches = [search for search in lit_searches if search.is_completed] 
            is_search_completed =  len(completed_searches) == lit_searches.count()
            if is_search_completed:
                search_status = "Completed"
            
        # article_ids = article_reviews.values_list("article__id", flat=True)
        # articles = Article.objects.filter(id__in=article_ids)
        # article_ser = ArticleSerializer(articles, many=True)
        reviews_ser = ArticleReviewSerializer(article_reviews, many=True)

        return Response({
            "article_reviews": reviews_ser.data,
            "search_id":search_id,
            "dates_filter_values_ser": dates_filter_values_ser.data,
            "search_status": search_status,

        }, status=status.HTTP_200_OK)
    



class CreateArticleCommentAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        # Extract data from the POST request
        comment_data = request.data
        text = comment_data["text"]
        article_id = comment_data["article.id"]
        search_id = comment_data["search_id"]
        article = Article.objects.filter(id =article_id).first()
        article_comment = ArticleComment.objects.create(
            user = request.user,
            text = text,
            article = article
        )
        article_comment.save()

        article = Article.objects.get(id=article_id)
        article_ser = ArticleSerializer(article)

        return Response({
            "message": "Article Comment Created Successfully",
            "updated_article": article_ser.data,
        }, status=status.HTTP_200_OK)
        


class UpdateAutomatedSearchAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):        
        if request.user.client:  
            lit_reviews = LiteratureReview.objects.filter(client=request.user.client)
            clients_list = []
        else:
            lit_reviews = LiteratureReview.objects.all()
            clients = Client.objects.all()
            clients_ser = ClientSerailizer(clients, many=True)
            clients_list = clients_ser.data

        devices = Device.objects.filter(literaturereview__in=lit_reviews).distinct("id")
        devices_ser = DeviceSerializer(devices, many=True)

        manufacturers =  Manufacturer.objects.all()
        manufacturers_ser = ManufacturerSerializer(manufacturers, many=True)

        not_isrecall = Q( Q(is_recall=None) | Q(is_recall=False) )
        not_isae = Q( Q(is_ae=None) | Q(is_ae=False) )
        not_recall_and_not_ae = Q( not_isrecall & not_isae)
        isrecall_or_isae = Q( Q(is_ae=True) | Q(is_recall=True) )


        lit_dbs = NCBIDatabase.objects.filter(not_recall_and_not_ae, is_archived=False)
        
        ae_databases = NCBIDatabase.objects.filter(isrecall_or_isae, is_archived=False)
        ae_basic_dbs = []
        ae_extra_dbs = []
        
        for ae_database in ae_databases:
            if ae_database.entrez_enum == "maude_recalls" or ae_database.entrez_enum == "embase" or ae_database.entrez_enum == "scholar":
                ae_basic_dbs.append(ae_database)
            else:
                ae_extra_dbs.append(ae_database)


        lit_dbs_ser = NCBIDatabaseSerializer(lit_dbs, many=True)
        ae_basic_dbs_ser = NCBIDatabaseSerializer(ae_basic_dbs, many=True)
        ae_extra_dbs_ser = NCBIDatabaseSerializer(ae_extra_dbs, many=True)


        search_id = self.kwargs.get('search_id')
        automated_search = AutomatedSearchProject.objects.filter(id = search_id).first()
        automated_search_ser = AutomatedSearchProjectSerializer(automated_search)

        return Response({
            "devices": devices_ser.data,
            "manufacturers": manufacturers_ser.data,
            "lit_dbs": lit_dbs_ser.data,
            "ae_basic_dbs": ae_basic_dbs_ser.data,
            "ae_extra_dbs": ae_extra_dbs_ser.data,
            "automated_search":automated_search_ser.data,
            "clients_list": clients_list,
        }, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        # Extract data from the POST request
        automation_data = request.data

        create_device = automation_data["createDevice"]
        create_manufacturer = automation_data["createManufacturer"]
        device_name = automation_data["deviceName"]
        manufacturer_name = automation_data["manufacturerName"]
        manufacturer = automation_data["selectedManufacturer"]
        classification = automation_data["classification"]
        markets = automation_data["markets"]
        selected_device = automation_data["selectedDevice"]
        selected_interval = automation_data["selectedInterval"]

        selected_dbs_json = request.POST.get('selectedDbs')
        selected_dbs = json.loads(selected_dbs_json)
        search_type = automation_data["searchType"]
        search_terms = automation_data["searchTerms"]
        search_file = automation_data["searchFile"]

        automatedSearchId = automation_data["automatedSearch"]
        automated_search_project = AutomatedSearchProject.objects.filter(id=automatedSearchId).first()

        if create_device == "true":
            # Your logic for creating a device
            if create_manufacturer == "true":
                manufacturer = Manufacturer.objects.create(name=manufacturer_name)
                manufacturer.save()
            else:
                manufacturer = get_object_or_404(Manufacturer, name=manufacturer)
                
            device = Device.objects.create(
                name = device_name,
                manufacturer = manufacturer,
                classification=classification,
                markets =markets
            )
            device.save()
        else:
            device = Device.objects.filter(id = selected_device).first()

        # update lit_review
        lit_review = automated_search_project.lit_review
        lit_review.device = device
        lit_review.save()

        # update interval
        automated_search_project.interval = selected_interval

        # update search_term_file
        if search_type == 'terms':
            automated_search_project.terms = search_terms
            automated_search_project.terms_file = ""
        else:
            if 'searchFile' in request.FILES:
                automated_search_project.terms_file = search_file
                automated_search_project.terms = ""

        # update selected_dbs
        # empty old dbs
        automated_search_project.databases_to_search.clear()
        # add new dbs
        for db in selected_dbs:
            db_item = NCBIDatabase.objects.filter(displayed_name = db).first()
            automated_search_project.databases_to_search.add(db_item)

        automated_search_project.last_run_date = timezone.now()
        automated_search_project.save()
        return Response({
            "message": "Automated Search Project Created Successfully"
        }, status=status.HTTP_200_OK)
    

class AutomatedSearchSaveToLibraryAPIView(APIView):
    permission_classes = [IsAuthenticated, ]
    def post(self, request, *args, **kwargs):    
        # Extract data from the POST request
        article_data = request.data    
        article_id = article_data["article_id"]
        search_id = article_data["search_id"]
        # article
        article = Article.objects.filter(id=article_id).first()

        library_entry  = LibraryEntry.objects.filter(
            article  = article,
        ).first()
        if library_entry:
            # delete library entry
            library_entry.delete()
        else:
            # create library entry
            library_entry  = LibraryEntry.objects.create(
                article  = article,
            )
            library_entry.save()

        article = Article.objects.get(id=article_id)
        article_ser = ArticleSerializer(article)

        return Response({
            "message": "Article Saved Successfully",
            "updated_article": article_ser.data,
        }, status=status.HTTP_200_OK)
