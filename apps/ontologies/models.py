from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Value
from django.db.models.fields import NOT_PROVIDED
from django.db.models.manager import Manager


def default_weight():
    return 1.0


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    weight = models.FloatField(default=1.0, blank=True, null=True)  # type: ignore

    objects: Manager = models.Manager()

    class Meta:
        abstract = True


class Ontology(BaseModel):
    class Meta:
        verbose_name_plural = "Ontologies"

    uri = models.URLField(primary_key=True)
    label = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label or self.uri


class Term(BaseModel):
    class Meta:
        verbose_name_plural = "Terms"
        indexes = [
            models.Index(fields=["uri"]),
            models.Index(fields=["ontology"]),
        ]

    uri = models.URLField(primary_key=True)
    ontology = models.ForeignKey(
        Ontology,
        related_name="terms",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    label = models.CharField(max_length=255, blank=True, null=True)
    definition = models.TextField(blank=True, null=True)
    subClassOf = ArrayField(
        models.URLField(),
        blank=True,
        null=True,
        default=list,
        help_text="List of URIs for parent classes (subClassOf relationships)",
    )

    weight = models.FloatField(default=1.0, blank=True, null=True)  # type: ignore
    is_favorite = models.BooleanField(default=False)  # type: ignore

    def __str__(self):
        return self.label or self.uri
