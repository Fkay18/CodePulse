from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from .models import Blog, Unit


def home(request):
    query = request.GET.get('q', '').strip()
    posts = Blog.objects.all()

    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(author__icontains=query)
        )

    posts = posts.order_by('-created_at')[:3]

    return render(request, 'blog/home.html', {'posts': posts, 'query': query})


def detail(request , id):
    post = Blog.objects.get(id=id)
    return render(request, 'blog/detail.html', {'post': post})


def contact(request):
    return render(request, 'blog/contact.html')


def about(request):
    return render(request, 'blog/about.html')


def articles(request):
    units = Unit.objects.annotate(article_count=Count('articles'))
    return render(request, 'blog/articles.html', {'units': units})


def unit_articles(request, slug):
    unit = get_object_or_404(Unit, slug=slug)
    posts = unit.articles.order_by('-created_at')
    return render(request, 'blog/unit_articles.html', {'unit': unit, 'posts': posts})
