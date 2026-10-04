from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import BlogForm, ClientSignUpForm, ProjectForm, UserProfileForm
from .models import Blog, Project, Unit, UserFollow, UserProfile

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


def detail(request, id):
    post = get_object_or_404(Blog, id=id)
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
            UserProfile.objects.get_or_create(user=user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = ClientSignUpForm()

    return render(request, 'blog/auth/signup.html', {'form': form})


@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    project_form = ProjectForm()

    if request.method == 'POST':
        if request.POST.get('action') == 'add_project':
            project_form = ProjectForm(request.POST, request.FILES)
            if user_profile.projects.count() >= 5:
                project_form.add_error(None, 'You can showcase up to five projects.')
            elif project_form.is_valid():
                project = project_form.save(commit=False)
                project.profile = user_profile
                project.save()
                return redirect(f'{reverse("profile")}#projects')
            form = UserProfileForm(instance=user_profile, user=request.user)
        else:
            form = UserProfileForm(request.POST, request.FILES, instance=user_profile, user=request.user)
            if form.is_valid():
                form.save()
                return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile, user=request.user)

    return render(request, 'blog/profile.html', {
        'form': form,
        'profile': user_profile,
        'projects': user_profile.projects.all(),
        'project_form': project_form,
    })


@login_required
def community(request):
    query = request.GET.get('q', '').strip()
    profiles = UserProfile.objects.select_related('user').annotate(
        followers_count=Count('user__follower_relationships', distinct=True),
    )
    if request.user.is_authenticated:
        profiles = profiles.exclude(user=request.user)

    if query:
        profiles = profiles.filter(
            Q(display_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(bio__icontains=query)
        )

    page_obj = Paginator(profiles.order_by('-followers_count', 'user__username'), 20).get_page(
        request.GET.get('page'),
    )
    profile_ids = [profile.user_id for profile in page_obj.object_list]
    following_ids = set()
    if request.user.is_authenticated:
        following_ids = set(
            UserFollow.objects.filter(
                follower=request.user,
                followed_id__in=profile_ids,
            ).values_list('followed_id', flat=True)
        )

    return render(request, 'blog/community.html', {
        'page_obj': page_obj,
        'query': query,
        'following_ids': following_ids,
    })


@login_required
def member_profile(request, username):
    member = get_object_or_404(get_user_model(), username=username)
    profile, _ = UserProfile.objects.get_or_create(user=member)
    is_following = request.user.is_authenticated and UserFollow.objects.filter(
        follower=request.user,
        followed=member,
    ).exists()

    return render(request, 'blog/member_profile.html', {
        'member': member,
        'profile': profile,
        'followers_count': UserFollow.objects.filter(followed=member).count(),
        'following_count': UserFollow.objects.filter(follower=member).count(),
        'is_following': is_following,
        'projects': profile.projects.all(),
    })


@login_required
def member_connections(request, username, connection):
    member = get_object_or_404(get_user_model(), username=username)
    if connection == 'followers':
        profiles = UserProfile.objects.filter(user__following_relationships__followed=member)
        heading = 'Followers'
    else:
        profiles = UserProfile.objects.filter(user__follower_relationships__follower=member)
        heading = 'Following'

    profiles = profiles.select_related('user').annotate(
        followers_count=Count('user__follower_relationships', distinct=True),
    ).order_by('-followers_count', 'user__username')
    page_obj = Paginator(profiles, 20).get_page(request.GET.get('page'))
    following_ids = set()
    if request.user.is_authenticated:
        following_ids = set(
            UserFollow.objects.filter(
                follower=request.user,
                followed_id__in=[profile.user_id for profile in page_obj.object_list],
            ).values_list('followed_id', flat=True)
        )
    return render(request, 'blog/member_connections.html', {
        'member': member,
        'connection': connection,
        'heading': heading,
        'page_obj': page_obj,
        'following_ids': following_ids,
    })


@login_required
@require_POST
def remove_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id, profile__user=request.user)
    project.delete()
    return redirect(f'{redirect("profile").url}#projects')


@login_required
@require_POST
def toggle_follow(request, username):
    member = get_object_or_404(get_user_model(), username=username)
    if member.pk != request.user.pk:
        follow, created = UserFollow.objects.get_or_create(
            follower=request.user,
            followed=member,
        )
        if not created:
            follow.delete()

    return redirect('member_profile', username=member.username)

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