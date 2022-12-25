from django import template
from director.models import Participant, Student

register = template.Library()


@register.simple_tag
def get_participant_true(lesson_pk):
    participants = Participant.objects.filter(lesson=lesson_pk, status=True)
    qty = 0
    for part in participants:
        qty += 1
    return qty


@register.simple_tag
def get_participant_names(lesson_pk, short=True):
    participants = Participant.objects.filter(lesson=lesson_pk)
    students_names = ''
    for student in participants:
        if not short:
            students_names += f'{student.student}' + ', '
        else:
            students_names += f'{student.student.surname} {student.student.name[0]}. {student.student.soname[0]}' + ', '
    return students_names[:-2]


@register.simple_tag
def get_students_qty_in_group(group_pk):
    students = Student.objects.filter(group__pk=group_pk, is_active=True).count()
    return students
