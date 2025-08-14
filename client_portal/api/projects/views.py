from rest_framework import generics
from client_portal.models import Project, Action
from lit_reviews.models import Device, LiteratureReview
from client_portal.api.projects.serializers import (
    ProjectSerializer,
    DeviceSerializer,
    ActionSerializer,
)
from django.db.models import Q
class ProjectsListAPIView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()

    def get_queryset(self):
        __filters = {"client": self.request.user.client}
        device_filter = self.request.query_params.get("device_filter")
        date_filter = self.request.query_params.get("date_filter")
        type_filter = self.request.query_params.get("type_filter")
        text_filter = self.request.query_params.get("search_term")
 
        if device_filter:
            __filters["lit_review__device__id"] = device_filter
        if date_filter:
            __filters["initial_complated_date"] = date_filter
        if type_filter:
            __filters["type"] = type_filter

        entries = self.queryset.filter(**__filters)

        if text_filter:
            entries = entries.filter(
                Q (
                    Q(client__name__icontains=text_filter) 
                    | 
                    Q(lit_review__device__name__icontains=text_filter)
                    | 
                    Q(lit_review__device__manufacturer__name__icontains=text_filter)
                )
            )

        return entries


class DeviceListAPIView(generics.ListAPIView):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()

    def get_queryset(self):
        lit_reviews = LiteratureReview.objects.filter(client__in=self.request.user.my_companies)
        return self.queryset.filter(id__in=lit_reviews.values("device__id")).distinct()



class MessagesListAPIView(generics.ListAPIView):
    serializer_class = ActionSerializer
    queryset = Action.objects.all()

    def get_queryset(self):
        
        __filters = {"project__client": self.request.user.client}
        # device_filter = self.request.query_params.get("device_filter")
        # date_filter = self.request.query_params.get("date_filter")
        # type_filter = self.request.query_params.get("type_filter")

        # if device_filter:
        #     __filters["lit_review__device__id"] = device_filter
        # if date_filter:
        #     __filters["initial_complated_date"] = date_filter
        # if type_filter:
        #     __filters["type"] = type_filter

        return self.queryset.filter(**__filters)
