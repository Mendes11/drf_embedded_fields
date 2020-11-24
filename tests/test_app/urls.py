from django.urls import path

from . import views

urlpatterns = [
    path("list/", views.ListChildView.as_view()),
    path("list/with-serializer/", views.ListChildWithSerializer.as_view())
]

