from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """
    Пагинатор, ограничивающий количество результатов в выдаче.
    """
    page_size_query_param = 'limit'
