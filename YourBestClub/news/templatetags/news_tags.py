from django import template
from django.core.cache import cache
from news.models import Post, Category
from django.db.models import Sum

register = template.Library()


@register.simple_tag
def get_news():
    news = cache.get('news')
    if not news:
        news = Post.objects.all()
        cache.set('news', news, 300)
    return news


# @register.simple_tag
# def get_balance(director_pk):
#     balance = DirectorPayment.objects.filter(director=director_pk).aggregate(Sum('amount'))['amount__sum']
#     return balance
