from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('articles/', views.articles, name='articles'),
    path('articles/<slug:slug>/', views.unit_articles, name='unit_articles'),
    path('<int:id>/', views.detail, name='detail'),
]