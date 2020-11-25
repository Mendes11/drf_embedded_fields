from rest_framework import serializers


def split_embed_relations(embed_fields_list):
    embed_relations = {}
    for field in embed_fields_list:
        field, *field_relations = field.split(".", maxsplit=1)
        embed_relations.setdefault(field, [])
        if field_relations:
            embed_relations[field].append(field_relations[0])
    return embed_relations


class EmbeddedFieldMixin:
    """
    EmbeddedField will either return to representation the original field or
    an embedded version of it.

    The returned value is determined by the parent embed_fields:
        When the embed_fields is present and this field name is a key in it,
        it returns the content from get_embedded_value.

        When it is not present or the field name is not in it, it will return
        the value rendered by the superclass.

    """
    embed_serializer_class = None
    embed = True
    embed_relations = []

    def get_embed_serializer_class(self):
        return self.embed_serializer_class or serializers.DictField

    def get_serializer(self, value, embed_relations, **kwargs):
        serializer_class = self.get_embed_serializer_class()
        if issubclass(serializer_class, serializers.BaseSerializer):
            context = self.parent.context
            context.update({"embed_fields": embed_relations})
            return serializer_class(context=context, **kwargs)
        return serializer_class(**kwargs)

    def to_embedded_representation(self, value, embed_relations):
        raise NotImplementedError()


class EmbeddedField(EmbeddedFieldMixin):
    def __init__(self, *args, embed=False, embed_relations=None,
                 embed_serializer_class=None, **kwargs):
        super(EmbeddedField, self).__init__(*args, **kwargs)
        self.embed_serializer_class = embed_serializer_class
        self.embed_relations = embed_relations or []
        self.embed = embed

    def to_representation(self, value):
        field_value = super(EmbeddedField, self).to_representation(value)
        if self.embed:
            serializer = self.get_serializer(field_value, self.embed_relations)
            embedded_value = self.to_embedded_representation(
                field_value, self.embed_relations
            )
            return serializer.to_representation(embedded_value)

        return field_value


class EmbeddableSerializerMixin:
    """
    Mixin to be used in serializers that contain EmbeddedFields.

    It will handle the control if a certain field should use the embedded
    content or the default.

    """

    def __init__(self, *args, **kwargs):
        super(EmbeddableSerializerMixin, self).__init__(*args, **kwargs)
        embed_fields = self.context.get("embed_fields", None)
        if embed_fields is None:
            assert "request" in self.context, "This serializer requires that the " \
                                              "request is sent in the context."
            embed_fields = self.context["request"].query_params.getlist("embed")

        self.embed_fields = split_embed_relations(
            embed_fields
        )
        for name, embed_relations in self.embed_fields.items():
            if name in self.fields:
                self.fields[name].embed = True
                self.fields[name].embed_relations = embed_relations

