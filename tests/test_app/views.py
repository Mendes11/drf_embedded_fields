from rest_framework.generics import ListCreateAPIView

from test_app.models import ChildModel
from test_app.serializers import ChildSerializer, ChildWithSerializerSerializer


class ListChildView(ListCreateAPIView):
    serializer_class = ChildSerializer
    queryset = ChildModel.objects.all()


class ListChildWithSerializer(ListCreateAPIView):
    serializer_class = ChildWithSerializerSerializer
    queryset = ChildModel.objects.all()
