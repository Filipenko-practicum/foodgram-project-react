from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
