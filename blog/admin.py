from django.contrib import admin
from .models import Blog, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'slug', 'author')
    list_filter = ('unit',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Blog, BlogAdmin)
