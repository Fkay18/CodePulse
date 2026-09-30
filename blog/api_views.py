from rest_framework import filters, viewsets

from .api_serializers import BlogSerializer
from .models import Blog


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.select_related('unit').order_by('-created_at')
    serializer_class = BlogSerializer
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ('title', 'content', 'author')
    ordering_fields = ('created_at', 'updated_at', 'title', 'author')
    ordering = ('-created_at',)