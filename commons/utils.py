from rest_framework.pagination import PageNumberPagination

class ResponsePagination(PageNumberPagination):
  page_size = 10
