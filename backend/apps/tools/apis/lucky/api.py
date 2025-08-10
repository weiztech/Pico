import random
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.app.permissions import AppPermission


class LuckyViewSet(ViewSet):
    permission_classes = [IsAuthenticated, AppPermission]
    url_prefix = 'lucky'
    api_basename = 'lucky_tools'

    @extend_schema(
        summary="Get a lucky number",
        description="Returns a random lucky number between 1 and 100.",
        responses=inline_serializer(
            name='LuckyNumberResponse',
            fields={
                'lucky_number': serializers.IntegerField(help_text="A lucky number between 1 and 100")
            }
        ),
        tags=['Lucky Tools']
    )
    @action(detail=False, methods=["get"])
    def lucky_number(self, request):
        """return lucky number between 1 and 100"""
        number = random.randint(1, 100)
        return Response({'lucky_number': number}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get a lucky text for today",
        description="Returns a lucky text phrase for the day.",
        responses=inline_serializer(
            name='LuckyTextResponse',
            fields={
                'lucky_text': serializers.CharField(help_text="A lucky text for the day")
            }
        ),
        tags=['Lucky Tools']
    )
    @action(detail=False, methods=["get"])
    def today_lucky_text(self, request):
        """
        return I'm feeling lucky! or I feel Great!
        :param request:
        :return:
        """
        texts = ["I'm feeling lucky!", "I feel Great!"]
        lucky_text = random.choice(texts)
        return Response({'lucky_text': lucky_text}, status=status.HTTP_200_OK)


