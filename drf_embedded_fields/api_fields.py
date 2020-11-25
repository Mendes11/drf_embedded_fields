from rest_framework import serializers
import requests
from rest_framework.exceptions import APIException

from drf_embedded_fields.base import EmbeddedField
from drf_embedded_fields.exceptions import ServiceValidationError, \
    CustomAPIException


class APIEmbeddedMixin:
    """
    Methods to do a HTTP request to retrieve an APIEmbeddedField content.
    """
    url = None
    included_headers = []
    method = "get"

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

    def get_url_kwargs(self, value):
        return {}

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


class APIResourceField(APIEmbeddedMixin, EmbeddedField):
    """
    This version of EmbeddedField will retrieve the embedded content from an
    external API.

    It is useful for distributed systems that need to retrieve data with more
    information for front-end purposes.
    """
    resource_url_id_key = "id"
    resource_id_attr = None

    def __init__(
            self, url, method="get", included_headers=None,
            resource_url_id_key=None, resource_id_attr=None, **kwargs
    ):
        super(APIResourceField, self).__init__(**kwargs)
        self.url = url
        self.method = method
        self.included_headers = included_headers or []
        self.resource_url_id_key = resource_url_id_key or self.resource_url_id_key
        self.resource_id_attr = resource_id_attr or self.resource_id_attr
        assert isinstance(self.included_headers, list), (
            "included_headers must be None or a list"
        )

    def get_url_kwargs(self, value):
        id_attr_val = getattr(value, self.resource_id_attr) if \
            self.resource_id_attr else str(value)
        return {self.resource_url_id_key: id_attr_val}


class APIResourceIntField(APIResourceField, serializers.IntegerField):
    pass


class APIResourceCharField(APIResourceIntField, serializers.CharField):
    pass


class APIResourceUUIDField(APIResourceField, serializers.UUIDField):
    pass


class APIResourceURLField(APIResourceField, serializers.URLField):
    """This Field will call the URL in it."""
    def __init__(self, url=None, *args, **kwargs):
        super(APIResourceURLField, self).__init__(url, *args, **kwargs)

    def get_url(self, value):
        return value
