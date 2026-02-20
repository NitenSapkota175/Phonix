"""
Standard DRF pagination classes for Phonix API.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SmallResultsPagination(PageNumberPagination):
    """For widgets like dashboard top-10 transactions."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10


class LargeResultsPagination(PageNumberPagination):
    """For reports and admin exports."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500
