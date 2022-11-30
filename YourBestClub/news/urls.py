from django.urls import path

from django.views.decorators.cache import cache_page
from .views import *

urlpatterns = [
    path('news/<int:pk>/', GetPost.as_view(extra_context={'title': 'Последние новости'}), name='post_detail'),
    path('news/', LastNews.as_view(extra_context={'title': 'Новости'}), name='last_news')
]
