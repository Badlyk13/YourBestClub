from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe

from .models import *


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('id', 'title')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'content', 'photo', 'views', 'category', 'created_at')
    search_fields = ('id', 'title', 'author', 'content', 'photo', 'views', 'category', 'created_at')