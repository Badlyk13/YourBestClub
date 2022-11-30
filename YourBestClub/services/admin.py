from django.contrib import admin
from django.utils.safestring import mark_safe

from services.models import Service


# Register your models here.

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'cost', 'periodicity')
    search_fields = ('id', 'title', 'description', 'cost', 'periodicity')
