from django import template

from news.models import Post, Category

register = template.Library()


@register.inclusion_tag('news/last_news_tpl.html')
def get_news():
    return {'posts': Post.objects.all()[:10]}
