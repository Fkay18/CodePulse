from django.http import HttpResponse
from django.shortcuts import render
from .models import Blog


def index(request):
    posts = Blog.objects.all()
    return render(request, 'blog/index.html', {'posts': posts})

