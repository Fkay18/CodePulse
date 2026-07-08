from django.http import HttpResponse
from django.shortcuts import render
from .models import Blog


def index(request):
    posts = Blog.objects.all()
    return render(request, 'blog/index.html', {'posts': posts})


def detail(request , id):
    post = Blog.objects.get(id=id)
    return render(request, 'blog/detail.html', {'post': post})