import inspect

import requests
from rest_framework import serializers
from rest_framework.exceptions import APIException

from drf_embedded_fields.exceptions import CustomAPIException, \
    ServiceValidationError


def split_embed_relations(embed_fields_list):
    embed_relations = {}
    for field in embed_fields_list:
        field, *field_relations = field.split(".", maxsplit=1)
        embed_relations.setdefault(field, [])
        if field_relations:
            embed_relations[field].append(field_relations[0])
    return embed_relations


class EmbeddedField:
    """
    EmbeddedField will either return to representation the original field or
    an embedded version of it.

    The returned value is determined by the parent embed_fields:
        When the embed_fields is present and this field name is a key in it,
        it returns the content from get_embedded_value.

        When it is not present or the field name is not in it, it will return
        the value rendered by the superclass.

    """

    def __init__(self, embed=False, embed_relations=None,
                 embed_serializer_class=None, **kwargs):
        super(EmbeddedField, self).__init__(**kwargs)
        self.embed_serializer_class = embed_serializer_class
        self.embed_relations = embed_relations or []
        self.embed = embed

    def get_embed_serializer_class(self):
        return self.embed_serializer_class or serializers.DictField

    def get_serializer(self, value, embed_relations):
        serializer_class = self.get_embed_serializer_class()
        if issubclass(serializer_class, serializers.BaseSerializer):
            context = {"embed_fields": embed_relations}
            return serializer_class(context=context)
        return serializer_class()

    def to_embedded_representation(self, value, embed_relations):
        raise NotImplementedError()

    def to_representation(self, value):
        field_value = super(EmbeddedField, self).to_representation(value)
        if self.embed:
            serializer = self.get_serializer(field_value, self.embed_relations)
            embedded_value = self.to_embedded_representation(
                field_value, self.embed_relations
            )
            return serializer.to_representation(embedded_value)

        return field_value


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


class APIEmbeddedMixin:
    """
    Methods to do a HTTP request to retrieve an APIEmbeddedField content.
    """

    def raise_from_response(self, response,
                            default_exception=APIException):
        status_code = response.status_code
        try:
            data = response.json()
        except Exception:
            raise default_exception()

        if status_code == 400:
            raise ServiceValidationError(data)

        elif "message" in data:
            exc = APIException(detail=data["message"], code=data.get("code"))
            exc.status_code = status_code
            raise exc

        elif isinstance(data, list) and status_code != 503:
            exc = CustomAPIException(data)
            exc.status_code = status_code
            raise exc

        raise default_exception()

    def parse_response(self, response):
        try:
            data = response.json()
        except AttributeError:
            data = None

        if 200 <= response.status_code < 300:
            return data
        self.raise_from_response(response)

    def get_from_api(self, url, method, headers, **kwargs):
        response = getattr(requests, method)(url, headers=headers, **kwargs)
        return self.parse_response(response)


class APIResourceEmbeddedMixin(APIEmbeddedMixin, EmbeddedField):
    """
    This version of EmbeddedField will retrieve the embedded content from an
    external API.

    It is useful for distributed systems that need to retrieve data with more
    information for front-end purposes.
    """

    def __init__(self, url, method="get", included_headers=None,
                 **kwargs):
        super(APIResourceEmbeddedMixin, self).__init__(**kwargs)
        self.url = url
        self.method = method
        self.included_headers = included_headers or []
        assert isinstance(self.included_headers, list), (
            "included_headers must be None or a list"
        )

    def get_url_kwargs(self, value):
        return {"id": str(value)}

    def get_url(self, value):
        return self.url.format(**self.get_url_kwargs(value))

    def get_request(self):
        """
        Retrieves the current request instance, to enable us to retrieve the
        headers to be used.
        :return:
        """
        return self.parent.context["request"]

    def to_embedded_representation(self, value, embed_relations):
        url = self.get_url(value)
        request = self.get_request()

        headers = {
            header: request.headers.get(header)
            for header in self.included_headers if request.headers.get(header)
        }
        params = {"embed": embed_relations}
        embedded_data = self.get_from_api(
            url, self.method, headers=headers, params=params
        )
        return embedded_data


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


class APIResourceEmbeddedField:
    def __new__(cls, child, *args, **kwargs):
        child_args = child._args
        child_kwargs = child._kwargs
        _args = [*args, *child_args]
        _kwargs = {
            **child_kwargs, **kwargs
        }
        return embedded_field_factory(type(child), APIResourceEmbeddedMixin)(
            *_args, **_kwargs
        )
