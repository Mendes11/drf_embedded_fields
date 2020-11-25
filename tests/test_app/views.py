from rest_framework.generics import ListCreateAPIView

from test_app.models import ChildModel, ManyModel
from test_app.serializers import ChildSerializer, ManySerializer


class ListChildView(ListCreateAPIView):
    serializer_class = ChildSerializer
    queryset = ChildModel.objects.all()


class ListChildWithSerializer(ListCreateAPIView):
    serializer_class = ChildSerializer
    queryset = ChildModel.objects.all()


class ListManyView(ListCreateAPIView):
    serializer_class = ManySerializer
    queryset = ManyModel.objects.all()
