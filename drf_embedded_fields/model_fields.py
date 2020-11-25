import inspect

from rest_framework import serializers

from drf_embedded_fields.base import EmbeddedField, EmbeddableSerializerMixin


class EmbeddableModelSerializer(
    EmbeddableSerializerMixin, serializers.ModelSerializer
):

    def _transform_field(self, field):
        new_class = EmbeddedModelField
        return new_class(*field._args, **field._kwargs)

    def get_fields(self):
        fields = super(EmbeddableModelSerializer, self).get_fields()
        for name, field in fields.items():
            if isinstance(field, serializers.PrimaryKeyRelatedField):
                fields[name] = self._transform_field(field)
        return fields


def embedded_field_factory(field, embedded_field_class=EmbeddedField):
    """
    Returns a new Field class with the EmbeddedFieldMixin subclassed.
    :param serializers.Field field: A Field class
    :return serializers.Field: A new Field class
    """
    assert inspect.isclass(field), "field argument must be a class."
    return type(
        field.__name__,
        (embedded_field_class, field),
        {}
    )


class EmbeddedModelField(EmbeddedField, serializers.PrimaryKeyRelatedField):
    def get_embed_serializer_class(self):
        model = self.get_queryset().model
        return type(
            "DefaultEmbeddedSerializer",
            (EmbeddableModelSerializer,),
            {
                'Meta': type(
                    'Meta', (), {
                        'model': model,
                        'fields': '__all__'
                    }
                )
            }
        )

    def to_embedded_representation(self, value, embed_relations):
        return super().to_internal_value(value)