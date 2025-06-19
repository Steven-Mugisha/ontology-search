from django.contrib.postgres.search import SearchVector
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView, Response

from apps.ontologies import models

from . import serializers


class OntologyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    queryset = models.Ontology.objects.all()
    serializer_class = serializers.OntologySerializer


class TermViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    queryset = models.Term.objects.all()
    serializer_class = serializers.TermSerializer


class CustomSearchPagination(PageNumberPagination):
    """Custom pagination for search results with configurable page size."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"


def rank_search_results(terms, query):
    """Rank based on uri, label, and definition."""
    query_lower = query.lower()
    results = []

    # First priority: URI matches
    uri_matches = [
        term for term in terms if query_lower in term.uri.lower().split("/")[-1]
    ]
    results.extend(uri_matches)

    # Second priority: Label matches (excluding those already in URI matches)
    label_matches = [
        term
        for term in terms
        if query_lower in term.label.lower() and term not in uri_matches
    ]
    results.extend(label_matches)

    # Third priority: Definition matches (excluding those already in URI or label matches)
    definition_matches = [
        term
        for term in terms
        if term.definition
        and query_lower in term.definition.lower()
        and term not in uri_matches
        and term not in label_matches
    ]
    results.extend(definition_matches)

    return results


class SearchView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        operation_id="Search Terms",
        description="Search for terms by their URI, label, or definition using a full-text search. Results are paginated and ranked by relevance.",
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                description="The search query string to match against term URIs, labels, or definitions.",
                required=True,
            ),
            OpenApiParameter(
                name="page",
                type=int,
                description="Page number for pagination (default: 1)",
                required=False,
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                description="Number of results per page (default: 20, max: 100)",
                required=False,
            ),
        ],
        responses={
            200: {"description": "Paginated search results"},
            400: {"description": "Bad Request"},
        },
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("query", "")
        if not query:
            return Response(
                {"error": "Query parameter 'query' is required."}, status=400
            )

        terms = models.Term.objects.annotate(
            search=SearchVector("uri", "label", "definition"),
        ).filter(search=query)

        # Rank the results: URI first, then label, then definition
        ranked_terms = rank_search_results(terms, query)

        # Apply pagination
        paginator = CustomSearchPagination()
        paginated_terms = paginator.paginate_queryset(ranked_terms, request)

        serializer = serializers.TermSerializer(paginated_terms, many=True)
        return paginator.get_paginated_response(serializer.data)
