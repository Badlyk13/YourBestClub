from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from YourBestClub import settings
from director.views import *

urlpatterns = [
    path('403Forbidden/', forbidden_403, name='403Forbidden'),
    path('', user_login, name='login'),
    path('login/', user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
    path('choice-type/', choice_type, name='choice_type'),
    path('register/<slug:user_type>/', register, name='register'),
    path('change_password/', change_password, name='change_password'),
    path('set_password/<int:user_type>/<int:pk>/', set_password, name='set_password'),


    path('add-details/<slug:user_type>', add_details, name='add_details'),
    path('<slug:user_type>/<int:pk>/detail', detail, name='detail'),
    path('<slug:user_type>/<int:pk>/edit_details', edit_details, name='edit_details'),
    path('<slug:user_type>/<int:pk>/delete/', delete, name='delete'),
    path('<slug:user_type>/<int:pk>/delete-confirm/', delete_confirm, name='delete_confirm'),
    ]

