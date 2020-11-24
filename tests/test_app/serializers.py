from rest_framework import serializers

from drf_embedded_fields.fields import EmbeddedField, APIResourceEmbeddedField
from test_app.models import ParentModel, ChildModel


class ExternalAPISerializer(serializers.Serializer):
    id = serializers.IntegerField()
    field_1 = serializers.CharField()


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentModel
        fields = "__all__"


class ChildSerializer(serializers.ModelSerializer):
    parent = EmbeddedField(
        field=serializers.PrimaryKeyRelatedField(
            queryset=ParentModel.objects.all()
        ),
        embedded_serializer=ParentSerializer()
    )
    external_api_field = APIResourceEmbeddedField(
        url="http://test-endpoint/api/v1/{id}/",
        field=serializers.IntegerField(),
        included_headers=["Authorization"]
    )
    class Meta:
        model = ChildModel
        fields = "__all__"


class ChildWithSerializerSerializer(serializers.ModelSerializer):
    parent = EmbeddedField(
        field=serializers.PrimaryKeyRelatedField(
            queryset=ParentModel.objects.all()
        ),
        embedded_serializer=ParentSerializer()
    )
    external_api_field = APIResourceEmbeddedField(
        url="http://test-endpoint/api/v1/{id}/",
        field=serializers.IntegerField(),
        embedded_serializer=ExternalAPISerializer()
    )

    class Meta:
        model = ChildModel
        fields = "__all__"
