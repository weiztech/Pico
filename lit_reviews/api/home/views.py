from rest_framework.generics import ListAPIView, UpdateAPIView, DestroyAPIView, CreateAPIView
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404 
from rest_framework.response import Response
from rest_framework import status, permissions
from datetime import datetime
from .serializers import (
    LiteratureReviewSerializer, 
    CustomerSettingsSerializer, 
    DeviceSerializer, 
    ManufacturerSerializer,
    SearchLabelOptionSerializer,
    SubscriptionSerializer,
    SupportRequestTicketSerializer,
)
from lit_reviews.models import (
    LiteratureReview, 
    ArticleReview, 
    CustomerSettings,
    DuplicationReport,
    SearchLabelOption,
    Device,
    Manufacturer,
    SupportRequestTicket,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from lit_reviews.api.pagination import CustomPagination
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from backend.logger import logger
from lit_reviews.helpers.generic import get_customer_settings
from lit_reviews.api.cutom_permissions import isProjectOwner
from accounts.models import Subscription
from lit_reviews.report_builder.prisma import prisma_summary_excel_context, prisma_excluded_articles_summary_context
from lit_reviews.tasks import send_email
from backend import settings


class LiteratureReviewSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class LiteratureReviewListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LiteratureReviewSerializer
    pagination_class = CustomPagination
    # pagination_class = LiteratureReviewSetPagination
    queryset = LiteratureReview.objects.all()
    ordering_fields = ('project__project_name', '-project__project_name')
    ordering = ('-project__project_name')
    filter_backends = (filters.OrderingFilter,)


    def get_queryset(self):
        if "literature_review_id" in self.request.session:
            del self.request.session["literature_review_id"]        
        # if user.client:
        #     queryset =  LiteratureReview.objects.filter(client=user.client).exclude(is_autosearch=True)
        # elif self.request.user.is_ops_member:
        #     queryset =  LiteratureReview.objects.filter(client__is_company=False).exclude(is_autosearch=True)
        # else:      
        #     queryset =  LiteratureReview.objects.all().exclude(is_autosearch=True)
        queryset = self.request.user.my_reviews()
        # exclude notebook projects and auto search projects
        queryset = queryset.exclude(project__project_name__iexact="notebook").exclude(is_autosearch=True)

        # text search filter
        text_filter = self.request.query_params.get("search", None)
        project_type = self.request.query_params.get("project_type", None)
        search_type = self.request.query_params.get("search_type", None)
        status = self.request.query_params.get("status", None)
        selected_start_date = self.request.query_params.get("selected_start_date", None)
        selected_end_date = self.request.query_params.get("selected_end_date", None)
        selected_device_type = self.request.query_params.get("selected_device_type", None)
        selected_manufacturer_type = self.request.query_params.get("selected_manufacturer_type", None)

        if text_filter:
            queryset = queryset.filter(Q(
                Q(project__project_name__icontains=text_filter) 
                | Q(device__name__icontains=text_filter) 
                | Q(client__name__icontains=text_filter) 
            )) 
        if project_type:
            pt_values = project_type.split(',')
            logger.info('project type values {}',pt_values)
            if "all" not in pt_values:
                queryset = queryset.filter(project__type__in=pt_values)

        if search_type:
            values = search_type.split(',')
            logger.info('Search Type values {}',values)
            if "all" not in values:
                filters = {}
                if "auto_search" in values:
                    filters = {"is_autosearch": True}
                if "regular" in values:
                    queryset = queryset.exclude(is_autosearch=True)

                queryset = queryset.filter(**filters)

        if status:
            values = status.split(',')
            logger.info('status filter values {}',values)
            if "all" not in values:
                status_filters = {}
                if "archived" in values:
                    status_filters = {"is_archived": True}
                if "active" in values:
                    queryset = queryset.exclude(is_archived=True)

                queryset = queryset.filter(**status_filters)

        # selected_start_date filter
        if selected_start_date:
            try:
                start_date = datetime.strptime(selected_start_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                logger.error(f"Invalid date format for selected_start_date: {selected_start_date}")

        # selected_end_date filter
        if selected_end_date:
            try:
                end_date = datetime.strptime(selected_end_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                logger.error(f"Invalid date format for selected_end_date: {selected_end_date}")


        # selected_device_type filter
        if selected_device_type:
            queryset = queryset.filter(device=selected_device_type)
        
        # selected_manufacturer_type filter
        if selected_manufacturer_type:
            queryset = queryset.filter(device__manufacturer=selected_manufacturer_type)
            

        # if display_autosearch:
        #     if user.is_staff:
        #         queryset =  LiteratureReview.objects.filter(is_autosearch=True)
        #     # else:
        #     #     return HttpResponseForbidden() 
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Get the paginated literature reviews data
        response = super().list(request, *args, **kwargs)
        # if user.client:
        #     queryset =  LiteratureReview.objects.filter(client=user.client).exclude(is_autosearch=True)
        # elif self.request.user.is_ops_member:
        #     queryset =  LiteratureReview.objects.filter(client__is_company=False).exclude(is_autosearch=True)
        # else:      
        #     queryset =  LiteratureReview.objects.all().exclude(is_autosearch=True)
        queryset = self.request.user.my_reviews()
        # exclude notebook projects and auto search projects
        queryset = queryset.exclude(project__project_name__iexact="notebook").exclude(is_autosearch=True)

        # Filter devices and manufacturers based on literature reviews in the queryset
        devices = Device.objects.filter(id__in=queryset.values_list('device_id', flat=True)).distinct()
        manufacturers = Manufacturer.objects.filter(id__in=devices.values_list('manufacturer_id', flat=True)).distinct()

        # Serialize the filtered devices and manufacturers
        device_serializer = DeviceSerializer(devices, many=True)
        manufacturer_serializer = ManufacturerSerializer(manufacturers, many=True)

        # Add serialized data to the response
        response.data['devices'] = device_serializer.data
        response.data['manufacturers'] = manufacturer_serializer.data

        # logger.info('Devices List {}',device_serializer.data)
        # logger.info('Manufacturer List {}',manufacturer_serializer.data)
        
        return response

class LiteratureReviewAnalysisView(APIView):

    def get(self, request, *args, **kwargs):
        # literature_reviews = LiteratureReview.objects.all()
        # if request.user.client:
        #     literature_reviews = literature_reviews.filter(client=request.user.client)
        # elif self.request.user.is_ops_member:
        #     literature_reviews = literature_reviews.filter(client__is_company=False)
        literature_reviews = request.user.my_reviews()

        # exclude notebook projects and auto search projects
        literature_reviews = literature_reviews.exclude(project__project_name__iexact="notebook").exclude(is_autosearch=True)

        related_articles = ArticleReview.objects.filter(search__literature_review__in=literature_reviews)
        total = related_articles.count()
        reviewed = related_articles.exclude(state="U").count()
        pending = related_articles.filter(state="U").count()
        completed = related_articles.filter(state__in=["I", "E"]).count()
            
        return Response({
            "counts": {
                "total": total,
                "reviewed": reviewed,
                "pending": pending,
                "completed": completed,
            },
            # coming soon
            "articles_chart": "",
            # coming soon
            "avrg_completion": "",
        }, status=status.HTTP_200_OK)
    

class CustomerSettingsAPIView(APIView):

    def get(self, request, *args, **kwargs):
        customer_settings = get_customer_settings(request.user)
        customer_settings_ser = CustomerSettingsSerializer(customer_settings)
        return Response(customer_settings_ser.data, status=status.HTTP_200_OK)
    

class UpdateCustomerSettingsAPIView(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = CustomerSettingsSerializer
    lookup_url_kwarg = "settings_id" 

    def get_queryset(self):
        if self.request.user.client:
            return CustomerSettings.objects.filter(client=self.request.user.client) 
        elif self.request.user.is_client:
            return CustomerSettings.objects.filter(client=None)
        elif self.request.user.is_staff or self.request.user.is_superuser:
            return CustomerSettings.objects.all()


class PrismaANDUserDataAPIView(APIView):

    def get(self, request, *args, **kwargs):
        lit_review_id = self.kwargs.get('id') 

        # User Subscription Data 

        subscription = Subscription.objects.filter(user=request.user).first()
        if subscription:
            user_subscription = SubscriptionSerializer(subscription).data 
        else:
            user_subscription = None
        
        # Prisma Data 
        if lit_review_id:
            # Get or create the duplication report related to the literature review
            duplication_report, created = DuplicationReport.objects.get_or_create(literature_review_id=lit_review_id)
            duplication_report_status =  duplication_report.status

            prisma_summary = prisma_summary_excel_context(lit_review_id)
            excluded_summary = prisma_excluded_articles_summary_context(lit_review_id)

            # Refactor prisma_summary into a list of dicts
            prisma_summary_dict = [
                {"label": row[0], "count": row[1]} for row in prisma_summary[1:]
            ]

            # Refactor excluded_summary into a list of dicts
            excluded_summary_dict = [
                {"reason": row[0], "count": row[1]} for row in excluded_summary[1:]
            ]

        else:
            prisma_summary_dict = None
            excluded_summary_dict = None 
            duplication_report_status = None


        return Response({
            "prisma_summary": prisma_summary_dict,
            "excluded_summary": excluded_summary_dict,
            "duplication_report_status": duplication_report_status,
            "user_subscription": user_subscription
        }, status=status.HTTP_200_OK)

        

class CustomLabelAPIView(APIView):
    def get(self, request, *args, **kwargs):
        customer_settings = get_customer_settings(request.user) 
        search_labels = SearchLabelOption.objects.filter(customer_settings=customer_settings)
        search_labels_serializer = SearchLabelOptionSerializer(search_labels, many=True)
                    
        response_data = {
            "search_labels":search_labels_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        customer_settings = get_customer_settings(request.user)
        # Retrieve labels from request
        custom_labels = request.data.get('custome_labels', [])
        saved_labels = []

        for label_data in custom_labels:
            label_id = label_data.get('id', None)
            label_text = label_data.get('label', '').strip()

            if not label_text:
                continue  # Skip empty labels

            # If an ID is provided, update the existing label
            if label_id:
                label_instance = SearchLabelOption.objects.filter(
                    id=label_id, customer_settings=customer_settings
                ).first()
                if label_instance:
                    label_instance.label = label_text
                    label_instance.save()
                    saved_labels.append(label_instance)
            else:
                # Otherwise, create a new label
                label_instance = SearchLabelOption.objects.create(
                    label=label_text, customer_settings=customer_settings
                )
                saved_labels.append(label_instance)

        # Serialize and return the updated list of labels
        search_labels_serializer = SearchLabelOptionSerializer(saved_labels, many=True)
        response_data = {
            "search_labels": search_labels_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)
    


class DestroySearchLabelOptionView(DestroyAPIView):
    queryset = SearchLabelOption.objects.all()
    lookup_url_kwarg = "custom_label_id"

    def destroy(self, request, *args, **kwargs):
        custom_label_obj = self.get_object()  # Retrieve the object to be deleted
        custom_label_id = custom_label_obj.id

        # Perform the deletion
        super().destroy(request, *args, **kwargs)

        # Return additional information after deletion
        return Response(
            {"id": kwargs.get("custom_label_id"), "object_id": custom_label_id},
            status=status.HTTP_200_OK,
        )


class SupportTicketCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SupportRequestTicketSerializer
    queryset = SupportRequestTicket.objects.all()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        
        logger.info(f'Support ticket created: {ticket.id} for user: {request.user.username}')
        send_email.delay("Support Ticket CiteMed.IO", ticket.description, to=settings.SUPPORT_EMAILS, from_email=request.user.email)
  
        return Response({
            'success': True,
            'ticket_id': ticket.id,
            'message': 'Support ticket created successfully.'
        }, status=status.HTTP_201_CREATED)
