"""
Shared utility helpers used across apps.
"""
import hashlib
import json


def make_hash(data: dict) -> str:
    """Stable SHA-256 hash of a dict (sorted keys)."""
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def get_client_ip(request) -> str:
    """Extract client IP address from request."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def paginate_queryset(queryset, request, serializer_class, page_size: int = 20):
    """Utility to paginate and serialize a queryset in a view."""
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = page_size
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        data = serializer_class(page, many=True).data
        return paginator.get_paginated_response(data)
    data = serializer_class(queryset, many=True).data
    from rest_framework.response import Response
    return Response(data)
