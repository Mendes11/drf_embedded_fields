import requests
from rest_framework import serializers
from rest_framework.exceptions import APIException

from drf_embedded_fields.exceptions import CustomAPIException, \
    ServiceValidationError


class EmbeddedField(serializers.Field):
    def __init__(self, field, embedded_serializer=None, **kwargs):
        super(EmbeddedField, self).__init__(**kwargs)
        self.original_field = field
        self.embedded_serializer = embedded_serializer or \
                                   serializers.DictField()

    def get_embedded_value(self, value):
        return value

    def to_representation(self, value):
        name = self.field_name

        embedded_fields = self.parent.context["request"].query_params.getlist(
            "embed")

        if name in embedded_fields:
            return self.embedded_serializer.to_representation(
                self.get_embedded_value(value)
            )

        return self.original_field.to_representation(value)


class APIEmbeddedMixin:
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


class APIResourceEmbeddedField(APIEmbeddedMixin, EmbeddedField):
    def __init__(self, url, field, method="get", included_headers=None,
                 **kwargs):
        super(APIResourceEmbeddedField, self).__init__(field, **kwargs)
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

    def get_embedded_value(self, value):
        url = self.get_url(value)
        request = self.parent.context["request"]

        headers = {
            header: request.headers.get(header)
            for header in self.included_headers if request.headers.get(header)
        }
        embedded_data = self.get_from_api(url, self.method, headers=headers)
        return super(APIResourceEmbeddedField, self).get_embedded_value(
            embedded_data
        )


class EmbeddableSerializer:
    def __init__(self, *args, **kwargs):
        super(EmbeddableSerializer, self).__init__(*args, **kwargs)
        assert "request" in self.context, "This serializer requires that the " \
                                          "request is sent in the context."
        request = self.context["request"]
        embedded_fields = request.query_params.getlist("embed")
