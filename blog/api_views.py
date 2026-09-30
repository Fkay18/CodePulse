from rest_framework import viewsets

from .api_serializers import BlogSerializer
from .models import Blog


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.select_related('unit').order_by('-created_at')
    serializer_class = BlogSerializer