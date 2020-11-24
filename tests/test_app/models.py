from django.db import models


class RootModel(models.Model):
    name = models.CharField(max_length=100)


class ParentModel(models.Model):
    str_field = models.CharField(max_length=100)
    root = models.ForeignKey(RootModel, on_delete=models.CASCADE)


class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    external_api_field = models.IntegerField()
