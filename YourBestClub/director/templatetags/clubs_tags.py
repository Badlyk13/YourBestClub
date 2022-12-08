from django import template
from director.models import Participant

register = template.Library()


@register.simple_tag
def get_participant_true(lesson_pk):
    participants = Participant.objects.filter(lesson=lesson_pk, status=True)
    qty = 0
    for part in participants:
        qty += 1
    return qty


@register.simple_tag
def get_participant_names(lesson_pk):
    participants = Participant.objects.filter(lesson=lesson_pk)
    students_names = ''
    for student in participants:
        students_names += f'{student.student}' + ', '
    return students_names[:-2]
