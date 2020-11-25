from rest_framework import serializers

from drf_embedded_fields.fields import EmbeddedField, APIResourceEmbeddedField, \
    EmbeddableModelSerializer
from test_app.models import ParentModel, ChildModel


class ExternalAPISerializer(serializers.Serializer):
    id = serializers.IntegerField()
    field_1 = serializers.CharField()


class ParentSerializer(EmbeddableModelSerializer):
    class Meta:
        model = ParentModel
        fields = "__all__"


class ChildSerializer(EmbeddableModelSerializer):
    external_api_field = APIResourceEmbeddedField(
        serializers.IntegerField(),
        "http://test-endpoint/api/v1/{id}/",
        included_headers=["Authorization"]
    )

    class Meta:
        model = ChildModel
        fields = "__all__"


class ChildSerializerWithSerializer(ChildSerializer):
    external_api_field = APIResourceEmbeddedField(
        serializers.IntegerField(),
        "http://test-endpoint/api/v1/{id}/",
        included_headers=["Authorization"],
    )
