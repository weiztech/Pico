

from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from lit_reviews.api.cutom_permissions import isNotClient
from lit_reviews.models import (
    LiteratureReview,
    Device,
    Client,
    Manufacturer,
)
from client_portal.models import Project

from lit_reviews.api.literature_review.serializers import (
    CreateLiteratureReviewSerailizer,
    DeviceSerializer,
    CreateClientSerailizer,
    LiteratureReviewSerializer,
    ManufacturerSerializer,
    CreateLivingReviewSerializer,
    LivingReviewSerializer,
)
from lit_reviews.api.cutom_permissions import isProjectOwner

class LiteratureReviewAPIListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LiteratureReviewSerializer
    queryset = LiteratureReview.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()        
        queryset = self.request.user.my_reviews()
        
        exclude_living_projects = self.request.query_params.get("exclude_living")
        device_filter = self.request.query_params.get("device", None)
        
        if device_filter:
            device_filter = int(device_filter)
            queryset = queryset.filter(device__id=device_filter)
        if exclude_living_projects:
            queryset = queryset.filter(parent_living_review__isnull=True, is_living_review=False)        
        return queryset


class ListDeviceAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(literaturereview__in=self.request.user.my_reviews()).distinct()
        return queryset
    

class GetDeviceAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()
    lookup_url_kwarg = "device_id"

    def get_object(self):
        device = super().get_object()
        reviews = LiteratureReview.objects.filter(device=device).all()
        user_reviews_ids = list(self.request.user.my_reviews().values_list("id", flat=True))
        if reviews.count() > 0 and reviews.filter(id__in=user_reviews_ids).count() == 0:
            raise PermissionError("You Don't Have Access To This Device")
        return device


class ListManufacturerAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ManufacturerSerializer
    queryset = Manufacturer.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        client_devices = Device.objects.filter(literaturereview__in=self.request.user.my_reviews())
        distinct_manufacturer_ids = client_devices.values_list('manufacturer', flat=True).distinct()
        queryset = Manufacturer.objects.filter(id__in=distinct_manufacturer_ids)
        return queryset

class ListClientAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateClientSerailizer
    queryset = Client.objects.all()

    def get_queryset(self):        
        queryset = self.request.user.my_companies
        return queryset
    
class CreateDeviceAPIView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer

class CreateClientAPIView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateClientSerailizer

class CreateLiteratureReviewAPIView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = CreateLiteratureReviewSerailizer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    

class CreateLivingReviewAPIView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateLivingReviewSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_obj = serializer.save()
        response_serializer = LivingReviewSerializer(created_obj)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    

    