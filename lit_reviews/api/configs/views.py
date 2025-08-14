from rest_framework.views import APIView
from rest_framework import permissions , status
from lit_reviews.models import LiteratureReview , ProjectConfig
from client_portal.models import Project
from rest_framework.response import Response 
from .serializers import ProjectConfigSerializer , ProjectConfigUpdateSerializer
from lit_reviews.api.cutom_permissions import isProjectOwner

class ProjectConfigAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ProjectConfigSerializer
    http_method_names = ['get']

    def get(self, request, *args, **kwargs): 
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        project_config = ProjectConfig.objects.filter(project__lit_review=lit_review,user=request.user).first()
        if not project_config:
            project = Project.objects.filter(lit_review=lit_review).first()
            if not project:
                project = Project.objects.create(lit_review=lit_review, client=lit_review.client, project_name="CM Project")

            project_config_serializer = ProjectConfigSerializer(data={"project":project.id,"user":request.user.id})
            project_config_serializer.is_valid(raise_exception=True) 
            project_config_serializer.save()
        else:
            project_config_serializer = ProjectConfigSerializer(project_config)

        return Response(project_config_serializer.data, status=status.HTTP_200_OK)
 
class UpdateProjectConfigAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ProjectConfigUpdateSerializer
    http_method_names = ['post']

    def post(self, request, *args, **kwargs): 
        lit_review_id = kwargs.get("id") 
        project_config_id = kwargs.get("config_id") 
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        project_config = ProjectConfig.objects.get(id=project_config_id) 
        sidebar_mode = request.data.get("sidebar_mode")
        project_config_serializer = ProjectConfigUpdateSerializer(data={"sidebar_mode":sidebar_mode},instance=project_config)
        project_config_serializer.is_valid(raise_exception=True) 
        project_config_serializer.save()
        return Response(project_config_serializer.data, status=status.HTTP_200_OK)

