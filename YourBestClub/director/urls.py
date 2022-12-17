from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from YourBestClub import settings
from director.finances import *
from director.views import *
from director.statistic import *

urlpatterns = [
    path('403Forbidden/', forbidden_403, name='403Forbidden'),
    path('', user_login, name='login'),
    path('login/', user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
    path('choice-type/', choice_type, name='choice_type'),
    path('register/<slug:user_type>/', register, name='register'),
    path('change_password/<slug:user_type>/<int:pk>/', change_password, name='change_password'),
    path('set_password/<slug:user_type>/<int:pk>/', set_password, name='set_password'),

    path('club/add-club/', club_add, name='club_add'),
    path('club/<int:pk>/detail/', club_detail, name='club_detail'),
    path('club/<int:pk>/edit/', club_edit, name='club_edit'),
    path('club/<int:pk>/delete/', club_delete, name='club_delete'),
    path('club/<int:pk>/delete-confirm/', club_delete_confirm, name='club_delete_confirm'),

    path('add-details/director/', add_details, name='add_details'),
    path('director/<int:pk>/detail', director_detail, name='detail'),
    path('director/<int:pk>/edit_details', director_edit_details, name='edit_details'),
    path('director/<int:pk>/delete/', director_delete, name='director_delete'),
    path('director/<int:pk>/delete-confirm/', director_delete_confirm, name='director_delete_confirm'),

    path('club/<int:pk>/subscription-add/', subscription_add, name='subscription_add'),
    path('club/<int:pk>/subscription-list/', subscription_list, name='subscription_list'),
    path('club/<int:pk>/subscription/<int:pk_subscription>/edit', subscription_edit, name='subscription_edit'),
    path('club/<int:pk>/subscription/<int:pk_subscription>/delete-confirm/', subscription_delete_confirm,
         name='subscription_delete_confirm'),

    path('club/<int:pk>/group-add/', group_add, name='group_add'),
    path('club/<int:pk>/group/<int:pk_group>/detail', group_detail, name='group_detail'),
    # path('club/<int:pk>/group/<int:pk_group>/statistic', group_statistic, name='group_statistic'),
    path('club/<int:pk>/group/<int:pk_group>/edit', group_edit, name='group_edit'),
    path('club/<int:pk>/groups/', group_list, name='groups'),
    path('club/<int:pk>/group/<int:pk_group>/delete/', group_delete, name='group_delete'),
    path('club/<int:pk>/group/<int:pk_group>/delete-confirm/', group_delete_confirm,
         name='group_delete_confirm'),

    path('club/<int:pk>/trainer-add/', trainer_add, name='trainer_add'),
    path('club/<int:pk>/trainer/<int:pk_trainer>/detail', trainer_detail, name='trainer_detail'),
    path('club/<int:pk>/trainer/<int:pk_trainer>/edit', trainer_edit, name='trainer_edit'),
    path('club/<int:pk>/trainers/', trainer_list, name='trainers'),
    path('club/<int:pk>/trainer/<int:pk_trainer>/delete/', trainer_delete, name='trainer_delete'),
    path('club/<int:pk>/trainer/<int:pk_trainer>/delete-confirm/', trainer_delete_confirm,
         name='trainer_delete_confirm'),

    path('club/<int:pk>/group/<int:pk_group>/student-add/', student_add, name='student_add'),
    path('club/<int:pk>/group/<int:pk_group>/student/<int:pk_student>/detail', student_detail, name='student_detail'),
    path('club/<int:pk>/group/<int:pk_group>/student/<int:pk_student>/edit', student_edit, name='student_edit'),
    path('club/<int:pk>/group/<int:pk_group>/students/', student_list, name='students'),
    path('club/<int:pk>/group/<int:pk_group>/student/<int:pk_student>/delete/', student_delete, name='student_delete'),
    path('club/<int:pk>/group/<int:pk_group>/student/<int:pk_tstudent>/delete-confirm/', student_delete_confirm,
         name='student_delete_confirm'),

    path('club/<int:pk>/schedule/', club_schedule, name='club_schedule'),
    path('club/<int:pk>/group/<int:pk_group>/schedule/', group_schedule, name='group_schedule'),

    path('club/<int:pk>/group/<int:pk_group>/add-lesson/', add_lesson, name='add_lesson'),
    path('club/<int:pk>/add-individual/', add_indiv_lesson, name='add_indiv_lesson'),

    path('club/<int:pk>/group/<int:pk_group>/lesson/<int:pk_lesson>/delete/', delete_lesson, name='delete_lesson'),
    path('club/<int:pk>/group/<int:pk_group>/lesson/<int:pk_lesson>/confirm_delete_lesson/', confirm_delete_lesson,
         name='confirm_delete_lesson'),

    path('club/<int:pk>/lesson/<pk_lesson>/students/', students_in_lesson, name='students_in_lesson'),

    path('club/<int:pk>/lesson/<pk_lesson>/participant/<int:pk_participant>/change_status_false/',
         change_status_false, name='change_status_false'),
    path('club/<int:pk>/lesson/<pk_lesson>/participant/<int:pk_participant>/change_status_true/',
         change_status_true, name='change_status_true'),

    path('club/<int:pk>/mailing/', club_mailing, name='club_mailing'),
    path('personal-mailing/<int:rec_type>/<int:pk_rec>/', personal_mailing, name='personal_mailing'),


    # ============================== STATISTICS =============================
    path('club/<int:pk>/statistic/', stat_home, name='stat_home'),
    path('club/<int:pk>/statistic/<int:period>/', stat_club_finances, name='stat_club_finances'),
    path('club/<int:pk>/statistic/<int:year>/<int:month>/', stat_club_finances_month, name='stat_club_finances_month'),
    path('club/<int:pk>/statistic/detail/', stat_detail, name='stat_detail'),
    path('club/<int:pk>/statistic/detail/download', download_detail, name='download_detail'),

    path('club/<int:pk>/statistic/lessons/<int:year>/', stat_lessons, name='stat_lessons'),
    path('club/<int:pk>/statistic/individuals/<int:year>/', stat_individuals, name='stat_individuals'),

    path('club/<int:pk>/statistic/students/<int:year>/', stat_registered_students, name='stat_registered_students'),
    path('club/<int:pk>/group/<int:pk_group>/statistic/<int:year>/', stat_group_students, name='stat_group_students'),

    # ============================== FINANCES =============================
    path('club/<int:pk>/finances/', fin_clubs, name='fin_clubs'),
    path('club/<int:pk>/finances/<type>/detail/', fin_details, name='fin_details'),

    path('club/<int:pk>/donation/', donat, name='donat'),
    path('club/<int:pk>/events/', events, name='events'),
    ]

