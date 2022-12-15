from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import *


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'surname', 'name', 'soname', 'phone', 'get_avatar', 'tgID', 'is_active')
    search_fields = ('id', 'surname', 'name', 'soname', 'phone', 'tgID', 'is_active')

    def get_avatar(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="40">')
        else:
            return '-'

    get_avatar.short_description = 'Аватар'


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('id', 'surname', 'name', 'soname', 'phone', 'get_avatar', 'club', 'tgID', 'is_active')
    search_fields = ('id', 'surname', 'name', 'soname', 'phone', 'tgID', 'is_active')

    def get_avatar(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="40">')
        else:
            return '-'

    get_avatar.short_description = 'Аватар'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'surname', 'name', 'soname', 'agent_name', 'agent_phone', 'group', 'get_avatar', 'tgID', 'is_active')
    search_fields = ('id', 'surname', 'name', 'soname', 'agent_name', 'agent_phone', 'birthday', 'tgID', 'is_active')

    def get_avatar(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="40">')
        else:
            return '-'

    get_avatar.short_description = 'Аватар'


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'city', 'address', 'description', 'get_avatar', 'director', 'get_services', 'is_active')
    search_fields = ('id', 'title', 'city', 'address', 'description', 'director')

    def get_services(self, obj):
        return "\n".join([p.services for p in obj.services.all()])

    def get_avatar(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="40">')
        else:
            return '-'

    get_avatar.short_description = 'Логотип'


@admin.register(ClubGroup)
class ClubGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'club', 'lesson_price', 'notification', 'get_subscription', 'get_avatar', 'is_active', )
    search_fields = ('id', 'title', 'description', 'club')

    def get_subscription(self, obj):
        return "\n".join([p.subscription for p in obj.subscription.all()])

    def get_avatar(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="40">')
        else:
            return '-'

    get_avatar.short_description = 'Аватар'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'dt', 'is_group', 'group')
    search_fields = ('id', 'dt', 'is_group', 'group')


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson', 'get_students', 'status')
    search_fields = ('id', 'lesson', 'student', 'status')

    def get_students(self, obj):
        return "\n".join([p.student for p in obj.student.all()])


@admin.register(ClubSubscription)
class ClubSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'club', 'title', 'qty_lesson', 'cost')
    search_fields = ('id', 'club', 'title', 'qty_lesson')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'club', 'amount', 'user', 'assignment', 'is_personal', 'yookassa_id', 'yookassa_status')
    search_fields = ('id', 'created_at','club', 'amount', 'user', 'assignment', 'is_personal')