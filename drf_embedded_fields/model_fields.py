import inspect

from rest_framework import serializers
from rest_framework.relations import MANY_RELATION_KWARGS

from drf_embedded_fields.base import EmbeddedField, EmbeddableSerializerMixin, \
    EmbeddedFieldMixin


class EmbeddableModelSerializer(
    EmbeddableSerializerMixin, serializers.ModelSerializer
):
    def get_fields(self):
        fields = super(EmbeddableModelSerializer, self).get_fields()
        for name, field in fields.items():
            if isinstance(field, serializers.PrimaryKeyRelatedField):
                fields[name] = EmbeddedModelField(
                    *field._args, **field._kwargs
                )
            elif isinstance(field, serializers.ManyRelatedField):
                kws = field._kwargs

                relation = kws.pop("child_relation")
                child_relation = EmbeddedModelField(
                    *relation._args, **relation._kwargs
                )

                list_kwargs = {'child_relation': child_relation}
                for key in kws.keys():
                    if key in MANY_RELATION_KWARGS:
                        list_kwargs[key] = kws[key]
                fields[name] = EmbeddedManyRelatedField(**list_kwargs)

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


class EmbeddedManyRelatedField(EmbeddedFieldMixin, serializers.ManyRelatedField):
    def __init__(self, *args, embed=False, embed_relations=None,
                 embed_serializer_class=None, **kwargs):
        super(EmbeddedManyRelatedField, self).__init__(*args, **kwargs)
        self.embed_serializer_class = embed_serializer_class
        self.embed_relations = embed_relations or []
        self.embed = embed

    def to_embedded_representation(self, iterable, embed_relations):

        self.child_relation.embed = True
        self.child_relation.embed_relations = embed_relations
        reprs = []
        for value in iterable:
            repr = self.child_relation.to_representation(value)
            reprs.append(repr)
        return reprs
    
    def to_representation(self, value):
        if self.embed:
            embedded_value = self.to_embedded_representation(
                value, self.embed_relations
            )
            return embedded_value
        return super(EmbeddedManyRelatedField, self).to_representation(value)
