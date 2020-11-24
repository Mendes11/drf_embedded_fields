from rest_framework import serializers

from drf_embedded_fields.fields import EmbeddedField


class EmbeddableSerializerMixin:
    """
    Mixin to be used in serializers that contain EmbeddedFields.

    It will handle the control if a certain field should use the embedded
    content or the default.

    """

    def __init__(self, *args, **kwargs):
        super(EmbeddableSerializerMixin, self).__init__(*args, **kwargs)
        assert "request" in self.context, "This serializer requires that the " \
                                          "request is sent in the context."
        request = self.context["request"]
        embedded_fields = request.query_params.getlist("embed")
        for field in embedded_fields:
            if self.fields.get(field):
                self.fields.get(field).embed = True


class EmbeddableSerializer(EmbeddableSerializerMixin, serializers.Serializer):
    pass


class EmbeddableModelSerializer(EmbeddableSerializerMixin,
                                serializers.ModelSerializer):
    def default_embedded_serializer(self, model):
        return type(
            "DefaultEmbeddedSerializer",
            (serializers.ModelSerializer,),
            {
                'Meta': type(
                    'Meta', (), {
                        'model': model,
                        'fields': '__all__'
                    }
                )
            }
        )(context=self.context)

    def get_fields(self):
        fields = super(EmbeddableModelSerializer, self).get_fields()
        embeddable_serializers = getattr(self.Meta, "embedded_serializers", {})
        for name, field in fields.items():
            if isinstance(field, serializers.PrimaryKeyRelatedField):
                serializer = embeddable_serializers.get(name)
                if serializer is None:
                    serializer = self.default_embedded_serializer(
                        field.get_queryset().model
                    )
                fields[name] = EmbeddedField(
                    field=field,
                    embedded_serializer=serializer
                )
        return fields
