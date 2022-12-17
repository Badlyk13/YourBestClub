from django.urls import path
from services.views import all_services

urlpatterns = [
    path('club/<int:pk>/services/', all_services, name='all_services'),
    ]

