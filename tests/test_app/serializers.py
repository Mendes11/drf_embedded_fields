from rest_framework import serializers

from drf_embedded_fields.api_fields import APIResourceIntField
from drf_embedded_fields.model_fields import EmbeddableModelSerializer
from test_app.models import ParentModel, ChildModel, ManyModel


class ExternalAPISerializer(serializers.Serializer):
    id = serializers.IntegerField()
    field_1 = serializers.CharField()


class ParentSerializer(EmbeddableModelSerializer):
    class Meta:
        model = ParentModel
        fields = "__all__"


class ChildSerializer(EmbeddableModelSerializer):
    external_api_field = APIResourceIntField(
        url="http://test-endpoint/api/v1/{id}/",
        included_headers=["Authorization"]
    )

    class Meta:
        model = ChildModel
        fields = "__all__"


class ChildSerializerWithSerializer(ChildSerializer):
    external_api_field = APIResourceIntField(
        url="http://test-endpoint/api/v1/{id}/",
        included_headers=["Authorization"],
    )


class ManySerializer(EmbeddableModelSerializer):
    class Meta:
        model = ManyModel
        fields = "__all__"
