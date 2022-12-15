from django import template
from django.core.cache import cache

from django.db.models import Sum

from director.models import Payment, Director

register = template.Library()


@register.simple_tag
def get_balance(pk):
    director = Director.objects.select_related('user').get(pk=pk)
    balance = Payment.objects.filter(user=director.user, is_personal=False).aggregate(Sum('amount'))
    return balance['amount__sum']
#
#
# @register.simple_tag
# def get_st_balance(student_pk):
#     balance = ClubsPay.objects.filter(student=student_pk).aggregate(Sum('amount'))['amount__sum']
#     return balance
#
#
# @register.simple_tag
# def get_trainers_list(group_pk):
#     lessons = Lesson.objects.filter(group=group_pk)
#     trainers_list = []
#     for lesson in lessons:
#         for trainer in lesson.trainer.all():
#             if trainer not in trainers_list:
#                 trainers_list.append(trainer)
#     return set(trainers_list)
