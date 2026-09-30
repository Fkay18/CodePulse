from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BlogForm, ClientSignUpForm
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


def client_signup(request):
    if request.method == 'POST':
        form = ClientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = ClientSignUpForm()

    return render(request, 'blog/auth/signup.html', {'form': form})

#Article Search View   
def search_articles(request):
    query = request.GET.get("q", "").strip()

    articles = Blog.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(author__icontains=query)
    ) if query else Blog.objects.none()

    articles = articles.order_by('-created_at')

    return render(request, "blog/search_results.html", {
        "articles": articles,
        "query": query,
    })
    
# Manage Articles View
@login_required
@permission_required('blog.view_blog', raise_exception=True)
def manage_articles(request):
    units = Unit.objects.all()

    return render(request, "blog/manage_articles.html", {
        "units": units,
    })
    
@login_required
@permission_required(('blog.view_blog', 'blog.change_blog'), raise_exception=True)
def edit_article_list(request):
    units = Unit.objects.all()

    return render(request, "blog/edit_article_list.html", {
        "units": units,
    })


@login_required
@permission_required(('blog.view_blog', 'blog.delete_blog'), raise_exception=True)
def delete_article_list(request):
    units = Unit.objects.all()

    return render(request, "blog/delete_article_list.html", {
        "units": units,
    })

# CRUD - Create
@login_required
@permission_required('blog.add_blog', raise_exception=True)
def add_articles(request):
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect("manage_articles")

    else:
        form = BlogForm()

    return render(request, "blog/add_articles.html", {
        "form": form,
    })

#CRUD - Update
@login_required
@permission_required(('blog.view_blog', 'blog.change_blog'), raise_exception=True)
def edit_article(request, slug):
    article = get_object_or_404(Blog, slug=slug)

    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES, instance=article)

        if form.is_valid():
            form.save()
            return redirect("manage_articles")

    else:
        form = BlogForm(instance=article)

    return render(request, "blog/edit_article.html", {
        "form": form,
        "article": article,
    })


#CRUD - Delete
@login_required
@permission_required(('blog.view_blog', 'blog.delete_blog'), raise_exception=True)
def delete_article(request, slug):
    article = get_object_or_404(Blog, slug=slug)

    if request.method == "POST":
        article.delete()
        return redirect("manage_articles")

    return render(request, "blog/delete_article.html", {
        "article": article,
    })
    
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            return render(request, "lab/login.html", {
                "error": "Invalid username or password."
            })
    return render(request, "lab/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")