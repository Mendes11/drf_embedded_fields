from unittest.mock import patch, call

from rest_framework.test import APIClient, APITestCase

from drf_embedded_fields.fields import APIEmbeddedMixin
from test_app.models import ParentModel, ChildModel, RootModel


class TestEmbeddedAPI(APITestCase):
    def setUp(self) -> None:
        self.c = APIClient()
        self.root = RootModel.objects.create(name="Test Root")
        self.parent1 = ParentModel.objects.create(str_field="Parent 1",
                                                  root=self.root)
        self.parent2 = ParentModel.objects.create(str_field="Parent 2",
                                                  root=self.root)
        self.child1 = ChildModel.objects.create(
            parent=self.parent1,
            external_api_field=1
        )
        self.child2 = ChildModel.objects.create(
            parent=self.parent1,
            external_api_field=2
        )
        self.child3 = ChildModel.objects.create(
            parent=self.parent2,
            external_api_field=1
        )
        self.embedded_external_1 = {
            "id": 1, "field_1": "TestExternalAPI"
        }
        self.embedded_external_2 = {
            "id": 2, "field_1": "TestExternalAPI2"
        }

    def test_retrieve_from_list_not_embedded(self):
        res = self.c.get("/list/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            [
                {"id": 1, "parent": 1, "external_api_field": 1},
                {"id": 2, "parent": 1, "external_api_field": 2},
                {"id": 3, "parent": 2, "external_api_field": 1},
            ]
        )

    def test_retrieve_from_list_embed_parent(self):
        res = self.c.get("/list/?embed=parent")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            [
                {"id": 1,
                 "parent": {
                     "id": 1,
                     "str_field": "Parent 1"
                 },
                 "external_api_field": 1},
                {"id": 2,
                 "parent": {
                     "id": 1,
                     "str_field": "Parent 1"
                 },
                 "external_api_field": 2},
                {"id": 3,
                 "parent": {
                     "id": 2,
                     "str_field": "Parent 2"
                 },
                 "external_api_field": 1},
            ]
        )

    @patch.object(APIEmbeddedMixin, "get_from_api")
    def test_retrieve_from_list_embed_external(self, get_from_api):
        get_from_api.side_effect = [
            self.embedded_external_1, self.embedded_external_1,
            self.embedded_external_2
        ]
        res = self.c.get("/list/?embed=external_api_field")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            [
                {"id": 1,
                 "parent": 1,
                 "external_api_field": self.embedded_external_1},
                {"id": 2,
                 "parent": 1,
                 "external_api_field": self.embedded_external_1},
                {"id": 3,
                 "parent": 2,
                 "external_api_field": self.embedded_external_2},
            ]
        )
        get_from_api.assert_has_calls(
            [
                call("http://test-endpoint/api/v1/1/", "get", headers={}),
                call("http://test-endpoint/api/v1/2/", "get", headers={}),
                call("http://test-endpoint/api/v1/1/", "get", headers={}),
            ],
        )

    @patch.object(APIEmbeddedMixin, "get_from_api")
    def test_retrieve_from_list_embed_external_used_headers(self, get_from_api):
        get_from_api.side_effect = [
            self.embedded_external_1, self.embedded_external_1,
            self.embedded_external_2
        ]
        res = self.c.get(
            "/list/?embed=external_api_field",
            **{"HTTP_AUTHORIZATION": "Bearer TokenHere",
               "HTTP_SOME_HEADER": "Test"}
        )
        self.assertEqual(res.status_code, 200)
        get_from_api.assert_has_calls(
            [
                call("http://test-endpoint/api/v1/1/", "get",
                     headers={"Authorization": "Bearer TokenHere"}),
                call("http://test-endpoint/api/v1/2/", "get",
                     headers={"Authorization": "Bearer TokenHere"}),
                call("http://test-endpoint/api/v1/1/", "get",
                     headers={"Authorization": "Bearer TokenHere"}),
            ],
        )

    @patch.object(APIEmbeddedMixin, "get_from_api")
    def test_retrieve_from_list_using_serializer(self, get_from_api):
        self.embedded_external_1["not_used_field"] = 1
        self.embedded_external_2["not_used_field"] = 2
        get_from_api.side_effect = [
            self.embedded_external_1, self.embedded_external_1,
            self.embedded_external_2
        ]
        res = self.c.get(
            "/list/with-serializer/?embed=external_api_field",
        )
        del self.embedded_external_1["not_used_field"]
        del self.embedded_external_2["not_used_field"]
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            [
                {"id": 1,
                 "parent": 1,
                 "external_api_field": self.embedded_external_1},
                {"id": 2,
                 "parent": 1,
                 "external_api_field": self.embedded_external_1},
                {"id": 3,
                 "parent": 2,
                 "external_api_field": self.embedded_external_2},
            ]
        )
