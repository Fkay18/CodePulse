from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('articles/', views.articles, name='articles'),
    path('articles/<slug:slug>/', views.unit_articles, name='unit_articles'),
    path('community/', views.community, name='community'),
    path('members/<str:username>/followers/', views.member_connections, {'connection': 'followers'}, name='member_followers'),
    path('members/<str:username>/following/', views.member_connections, {'connection': 'following'}, name='member_following'),
    path('projects/<int:project_id>/remove/', views.remove_project, name='remove_project'),
    path('members/<str:username>/', views.member_profile, name='member_profile'),
    path('members/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('<int:id>/', views.detail, name='detail'),
    path("search/", views.search_articles, name="search_articles"),
    path('manage_articles/', views.manage_articles, name='manage_articles'),
    path('add_articles/', views.add_articles, name='add_articles'),
    path('edit_article_list/', views.edit_article_list, name='edit_article_list'),
    path('delete_article_list/', views.delete_article_list, name='delete_article_list'),
    path('edit_article/<slug:slug>/', views.edit_article, name='edit_article'),
    path('delete_article/<slug:slug>/', views.delete_article, name='delete_article'),
    path('login/', auth_views.LoginView.as_view(template_name='blog/auth/login.html'), name='login'),
    path('signup/', views.client_signup, name='client_signup'),
    path('profile/', views.profile, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='blog/auth/password_reset_form.html',
            email_template_name='blog/auth/password_reset_email.txt',
            subject_template_name='blog/auth/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='blog/auth/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='blog/auth/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='blog/auth/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]