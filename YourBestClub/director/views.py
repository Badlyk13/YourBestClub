from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError

from YourBestClub.settings import TELEGRAM_BOT_URI
from YourBestClub.utils import finding_user, create_password
from director.forms import UserLoginForm, UserCreateForm, DirectorForm, TrainerForm, StudentForm, CreateClubForm, \
    CreateGroupForm, CreateSubscriptionForm, CreateLessonForm, CreateIndividualLessonForm, ClubMailingForm, \
    PersonalMailingForm
from director.models import Director, Trainer, Student, ClubGroup, Club, ClubSubscription, Lesson, Participant, Payment
from PIL import Image


# Create your views here.
def forbidden_403(request):
    return render(request, 'director/403_Forbidden.html')


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Успешная авторизация!')
            if request.user.director:
                return redirect('detail', pk=user.director.pk)
            if request.user.trainer:
                return redirect('detail', user_type='trainer', pk=user.trainer.pk)
            if request.user.student:
                return redirect('detail', user_type='student', pk=user.student.pk)
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error)
    else:
        if request.user.is_authenticated:
            print('You authenticated')
            if request.user.director:
                return redirect('detail', pk=request.user.director.pk)
            if request.user.trainer:
                return redirect('detail', user_type='trainer', pk=request.user.trainer.pk)
            if request.user.student:
                return redirect('detail', user_type='student', pk=request.user.student.pk)

    form = UserLoginForm()
    return render(request, 'director/registration/login.html', {'form': form, 'title': 'Авторизация'})


def choice_type(request):
    return render(request, 'director/registration/choice_type.html', {'title': "Выберите ваш статус:"})


def register(request, user_type):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Шаг 1 успешно пройден!')
            return redirect('add_details', user_type=user_type)
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error + ' ' + field)
    else:
        if request.user.is_authenticated:
            return redirect(f'{user_type}_detail')
        else:
            form = UserCreateForm()
    return render(request, 'director/registration/registration.html',
                  {'title': 'Регистрация', 'form': form})


@login_required
def add_details(request):
    form = ''
    if request.method == 'POST':
        form = DirectorForm(request.POST, request.FILES)

        if form.is_valid():
            form.save(commit=False)
            form.instance.user = request.user
            reg_user = form.save()
            messages.success(request, 'Шаг 2 успешно пройден! Последний шаг...')
            return redirect('director_detail', pk=reg_user.pk)
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error + ' ' + field)
    else:
        form = DirectorForm()
        return render(request, f'director/director/add.html',
                      {'title': 'Шаг 2. Личные данные', 'form': form})


@login_required
def director_edit_details(request, pk):
    if request.method == 'POST':
        form = DirectorForm(request.POST, request.FILES, instance=Director.objects.get(pk=pk))
        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения внесены!')
            return redirect('detail', pk=pk)
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error + ' ' + field)
    else:
        form = DirectorForm(instance=Director.objects.get(pk=pk))
        director = Director.objects.get(pk=pk)
        return render(request, f'director/director/edit.html',
                      {'title': 'Личные данные', 'form': form, 'director': director})


@login_required
def director_detail(request, pk):
    director = Director.objects.get(pk=pk)
    link = f"{TELEGRAM_BOT_URI}c{pk}d"
    return render(request, f'director/director/detail.html',
                  {'title': 'Личный кабинет', 'director': director, 'link': link})


@login_required
def director_delete(request, pk):
    director = Director.objects.select_related('user').get(pk=pk)
    balance = Payment.objects.filter(user=director.user, is_personal=False).aggregate(Sum('amount'))['amount__sum']
    if balance is None:
        balance = 0
    return render(request, f'director/registration/delete.html',
                  {'title': 'Удаление', 'user_data': director, 'user_type': 'director', 'balance': balance})


@login_required
def director_delete_confirm(request, pk):
    user = Director.objects.get(pk=pk)
    user.delete()
    return redirect('login')


@login_required
def change_password(request, user_type, pk):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            user_data, user_type = finding_user(user)
            messages.success(request, 'Пароль обновлен!')
            return redirect('detail', user_type=user_type, pk=user_data.pk)
        else:
            for field in form.errors:
                messages.error(request, form.errors[field].as_text())
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'director/registration/change_password.html', {'title': 'Изменение пароля', 'form': form})


@login_required
def set_password(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user_data, user_type = finding_user(user)
            messages.success(request, 'Пароль установлен!')
            return redirect('detail', user_type=user_type, pk=user_data.pk)
    else:
        form = SetPasswordForm(request.user)
        return render(request, 'director/registration/set_password.html', {'title': 'Создание пароля', 'form': form})


# ===================================== CLUB =================================
@login_required
def club_add(request):
    if request.method == 'POST':
        form = CreateClubForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(commit=False)
            form.instance.director = request.user.director
            club = form.save()
            messages.success(request, 'Клуб добавлен!')
            return redirect('detail', user_type='director', pk=request.user.director.pk)
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error)
    else:
        form = CreateClubForm()
    return render(request, 'director/club/add.html',
                  {'title': 'Добавление клуба', 'form': form, 'director': request.user.director})


@login_required
def club_detail(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, 'director/club/detail.html',
                      {'title': f'{club.title}', 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def club_edit(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        if request.method == 'POST':
            form = CreateClubForm(request.POST, request.FILES, instance=club)
            if form.is_valid():
                form.save(commit=False)
                form.instance.director = request.user.director
                club = form.save()
                messages.success(request, 'Изменения внесены!')
                return redirect('detail', user_type='director', pk=club.director.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error)
        else:
            form = CreateClubForm(instance=club)
        return render(request, 'director/club/add.html',
                      {'title': 'Редактирование клуба', 'form': form, 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def club_delete(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, f'director/club/delete.html',
                      {'title': 'Удаление клуба', 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def club_delete_confirm(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        club.delete()
        return redirect('detail', user_type='director', pk=club.director.pk)
    else:
        return redirect('403Forbidden')


# ===================================== Club Subscription =================================
@login_required
def subscription_add(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    form = ''
    if request.user.director == club.director:
        if request.method == 'POST':
            form = CreateSubscriptionForm(request.POST, request.FILES)
            if form.is_valid():
                form.save(commit=False)
                form.instance.club = club
                reg_subscription = form.save()
                messages.success(request, 'Абонемент успешно добавлен!')
                return redirect('subscription_list', pk=club.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
        else:
            form = CreateSubscriptionForm()
            return render(request, f'director/club/subscription/add.html',
                          {'title': 'Добавление абонемента', 'form': form, 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def subscription_list(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, 'director/club/subscription/list.html',
                      {'title': 'Абонементы', 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def subscription_edit(request, pk, pk_subscription):
    club = Club.objects.select_related('director').get(pk=pk)
    form = ''
    if request.user.director == club.director:
        subscription = ClubSubscription.objects.get(pk=pk_subscription)
        if request.method == 'POST':
            form = CreateSubscriptionForm(request.POST, request.FILES, instance=subscription)
            if form.is_valid():
                form.save()
                messages.success(request, 'Данные успешно обновлены!')
                return redirect('subscription_list', pk=club.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
        else:
            form = CreateSubscriptionForm(instance=subscription)
            return render(request, f'director/club/subscription/edit.html',
                          {'title': 'Редактирование абонемента', 'form': form, 'subscription': subscription})
    else:
        return redirect('403Forbidden')


@login_required
def subscription_delete_confirm(request, pk, pk_subscription):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        subscription = ClubSubscription.objects.get(pk=pk_subscription)
        subscription.delete()
        return redirect('subscription_list', pk=club.pk)


# ===================================== CLUB GROUP =================================
@login_required
def group_add(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    form = ''
    if request.user.director == club.director:
        if request.method == 'POST':
            form = CreateGroupForm(request.POST, request.FILES)
            if form.is_valid():
                form.save(commit=False)
                form.instance.club = club
                reg_group = form.save()
                messages.success(request, 'Группа успешно добавлена!')
                return redirect('group_detail', pk=club.pk, pk_group=reg_group.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
        else:
            form = CreateGroupForm()
            form.fields['subscription'].queryset = club.clubsubscription_set.all()
            return render(request, f'director/group/add.html',
                          {'title': 'Добавление группы', 'form': form, 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def group_list(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, 'director/group/list.html',
                      {'title': 'Группы', 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def group_detail(request, pk, pk_group):
    club = Club.objects.select_related('director').get(pk=pk)
    group = ClubGroup.objects.get(pk=pk_group)
    if request.user.director == club.director:
        return render(request, 'director/group/detail.html',
                      {'title': group.title, 'group': group})
    else:
        return redirect('403Forbidden')


@login_required
def group_edit(request, pk, pk_group):
    club = Club.objects.select_related('director').get(pk=pk)
    form = ''
    if request.user.director == club.director:
        group = ClubGroup.objects.get(pk=pk_group)
        if request.method == 'POST':
            form = CreateGroupForm(request.POST, request.FILES, instance=group)
            if form.is_valid():
                form.save()
                messages.success(request, 'Данные успешно обновлены!')
                return redirect('group_detail', pk=club.pk, pk_group=group.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
        else:
            form = CreateGroupForm(instance=group)
            # form.fields['subscription'].queryset = club.clubsubscription_set.all()
            return render(request, f'director/group/edit.html',
                          {'title': 'Редактирование группы', 'form': form, 'group': group})
    else:
        return redirect('403Forbidden')


@login_required
def group_delete(request, pk, pk_group):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        group = ClubGroup.objects.get(pk=pk_group)
        return render(request, f'director/registration/delete.html',
                      {'title': 'Удаление', 'user_data': group, 'user_type': 'group'})
    else:
        return redirect('403Forbidden')


@login_required
def group_delete_confirm(request, pk, pk_group):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        group = ClubGroup.objects.get(pk=pk_group)
        group.delete()
        return redirect('groups', pk=club.pk)


# ===================================== TRAINER =================================
@login_required
def trainer_add(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    form = ''
    if request.user.director == club.director:
        if request.method == 'POST':
            form = TrainerForm(request.POST, request.FILES)
            if form.is_valid():
                form.save(commit=False)
                form.instance.club = club
                reg_user = form.save()
                messages.success(request, 'Тренер успешно добавлен!')
                return redirect('trainer_detail', pk=club.pk, pk_trainer=reg_user.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
                    form = TrainerForm()
                    return render(request, f'director/trainer/add.html',
                                  {'title': 'Добавление тренера', 'form': form, 'club': club})
        else:
            form = TrainerForm()
            return render(request, f'director/trainer/add.html',
                          {'title': 'Добавление тренера', 'form': form, 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def trainer_list(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, 'director/trainer/list.html',
                      {'title': 'Тренера', 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def trainer_detail(request, pk, pk_trainer):
    club = Club.objects.select_related('director').get(pk=pk)
    trainer = Trainer.objects.get(pk=pk_trainer)
    if request.user.director == club.director:
        return render(request, 'director/trainer/detail.html',
                      {'title': trainer, 'trainer': trainer})
    else:
        return redirect('403Forbidden')


@login_required
def trainer_edit(request, pk, pk_trainer):
    club = Club.objects.select_related('director').get(pk=pk)
    form = ''
    if request.user.director == club.director:
        trainer = Trainer.objects.get(pk=pk_trainer)
        if request.method == 'POST':
            form = TrainerForm(request.POST, request.FILES, instance=trainer)
            if form.is_valid():
                form.save()
                messages.success(request, 'Данные успешно внесены!')
                return redirect('trainer_detail', pk=club.pk, pk_trainer=trainer.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
                    form = TrainerForm()
                    return render(request, f'director/trainer/edit.html',
                                  {'title': 'Редактирование тренера', 'form': form, 'club': club})
        else:
            form = TrainerForm(instance=trainer)
            return render(request, f'director/trainer/edit.html',
                          {'title': 'Редактирование тренера', 'form': form, 'trainer': trainer})
    else:
        return redirect('403Forbidden')


@login_required
def trainer_delete(request, pk, pk_trainer):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        trainer = Trainer.objects.get(pk=pk_trainer)
        return render(request, f'director/registration/delete.html',
                      {'title': 'Удаление', 'user_data': trainer, 'user_type': 'trainer'})
    else:
        return redirect('403Forbidden')


@login_required
def trainer_delete_confirm(request, pk, pk_trainer):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        user = Trainer.objects.get(pk=pk_trainer)
        user.delete()
        return redirect('trainers', pk=club.pk)


# ===================================== STUDENT =================================
@login_required
def student_add(request, pk, pk_group):
    club = Club.objects.select_related('director').get(pk=pk)
    group = ClubGroup.objects.get(pk=pk_group)
    form = ''
    if request.user.director == club.director:
        if request.method == 'POST':
            form = StudentForm(request.POST, request.FILES)
            if form.is_valid():
                form.save(commit=False)
                form.instance.group = group
                reg_user = form.save()
                messages.success(request, 'Ученик успешно добавлен!')
                return redirect('student_detail', pk=club.pk, pk_group=group.pk, pk_student=reg_user.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
                    form = StudentForm()
                    return render(request, f'director/student/add.html',
                                  {'title': 'Добавление ученика', 'form': form, 'group': group})
        else:
            form = StudentForm()
            form.fields['group'].queryset = ClubGroup.objects.filter(pk=pk_group)
            return render(request, f'director/student/add.html',
                          {'title': 'Добавление ученика', 'form': form, 'club': club})
    else:
        return redirect('403Forbidden')


@login_required
def student_list(request, pk, pk_group):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    if request.user.director == group.club.director:
        return render(request, 'director/student/list.html',
                      {'title': 'Ученики', 'group': group})
    else:
        return redirect('403Forbidden')


@login_required
def student_detail(request, pk, pk_group, pk_student):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    student = Student.objects.get(pk=pk_student)
    qty_lesson = Participant.objects.filter(student=student, status=True, lesson__is_group=True, lesson__dt__lt=timezone.now()).count()
    qty_lesson_ind = Participant.objects.filter(student=student, status=True, lesson__is_group=False, lesson__dt__lt=timezone.now()).count()
    if request.user.director == group.club.director:
        return render(request, 'director/student/detail.html',
                      {'title': student, 'student': student, 'qty_lesson': qty_lesson, 'qty_lesson_ind': qty_lesson_ind})
    else:
        return redirect('403Forbidden')


@login_required
def student_edit(request, pk, pk_group, pk_student):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    form = ''
    if request.user.director == group.club.director:
        student = Student.objects.get(pk=pk_student)
        if request.method == 'POST':
            form = StudentForm(request.POST, request.FILES, instance=student)
            if form.is_valid():
                form.save()
                messages.success(request, 'Данные успешно изменены!')
                return redirect('student_detail', pk=group.club.pk, pk_group=group.pk, pk_student=student.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error + ' ' + field)
                    form = StudentForm()
                    return render(request, f'director/student/edit.html',
                                  {'title': 'Редактирование ученика', 'form': form, 'pk_group': pk_group})
        else:
            form = StudentForm(instance=student)
            form.fields['group'].queryset = ClubGroup.objects.filter(club=group.club)
            return render(request, f'director/student/edit.html',
                          {'title': 'Редактирование ученика', 'form': form, 'student': student})
    else:
        return redirect('403Forbidden')


@login_required
def student_delete(request, pk, pk_group, pk_student):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    if request.user.director == group.club.director:
        student = Student.objects.get(pk=pk_student)
        return render(request, f'director/registration/delete.html',
                      {'title': 'Удаление', 'user_data': student, 'user_type': 'student'})
    else:
        return redirect('403Forbidden')


@login_required
def student_delete_confirm(request, pk, pk_group, pk_student):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    if request.user.director == group.club.director:
        student = Student.objects.get(pk=pk_student)
        student.is_active = False
        student.no_active_at = timezone.now()
        student.save()
        return redirect('students', pk=group.club.pk, pk_group=pk_group)
    else:
        return redirect('403Forbidden')

    # -------------------------------------- РАСПИСАНИЕ. ДОБАВИТЬ УРОК  -----------------------------


@login_required
def add_lesson(request, pk, pk_group):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    if request.user.director == group.club.director:
        if request.method == 'POST':
            form = CreateLessonForm(request.POST)
            if form.is_valid():
                qty_weeks = form.cleaned_data.get('qty_weeks')
                if qty_weeks == 0:
                    lesson = Lesson.objects.create(dt=form.cleaned_data['dt'], is_group=True, group=group)
                    lesson.trainer.add(*form.cleaned_data['trainer'])
                else:
                    for i in range(0, qty_weeks):
                        dt = form.cleaned_data.get('dt') + timezone.timedelta(days=7*i)
                        lesson = Lesson.objects.create(dt=dt, is_group=True, group=group)
                        lesson.trainer.add(*form.cleaned_data['trainer'])
                messages.success(request, 'Занятие добавлено!')
                return redirect('group_schedule', pk=pk, pk_group=pk_group)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error)
        else:
            form = CreateLessonForm()
            form.fields['trainer'].queryset = Trainer.objects.filter(club=group.club)
        return render(request, 'director/club/schedule/add_lesson.html',
                      {'form': form, 'group': group, 'current_date': timezone.datetime.now()})
    else:
        return redirect('403Forbidden')


@login_required
def delete_lesson(request, pk, pk_group, pk_lesson):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    if request.user.director == group.club.director:
        lesson = get_object_or_404(Lesson, pk=pk_lesson)
        return render(request, 'director/club/schedule/delete_lesson.html', {'title': 'Удаление занятия', 'lesson': lesson, 'group': group})
    else:
        return redirect('403Forbidden')


@login_required
def confirm_delete_lesson(request, pk, pk_group, pk_lesson):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    if request.user.director == group.club.director:
        lesson = get_object_or_404(Lesson, pk=pk_lesson)
        lesson.delete()
        participants = Participant.objects.filter(lesson=pk_lesson)
        participants.delete()
        groups = ClubGroup.objects.filter(pk=pk_group)
        lessons_group = Lesson.objects.filter(group__in=ClubGroup.objects.filter(club=group.club), is_group=True)
        individuals_participants = Participant.objects.filter(
            student__in=Student.objects.filter(group__in=ClubGroup.objects.filter(club=group.club)))

        return redirect('group_schedule', pk=group.club.pk, pk_group=pk_group)
    else:
        return redirect('403Forbidden')


# -------------------------------------- РАСПИСАНИЕ. ДОБАВИТЬ ИНДИВ  -----------------------------
@login_required
def add_indiv_lesson(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    pk_group = ''
    tr_set = []
    if request.user.director == club.director:
        if request.method == 'POST':
            form = CreateIndividualLessonForm(request.POST)
            if form.is_valid():
                trainer = form.cleaned_data['trainer']
                lesson = Lesson.objects.create(dt=form.cleaned_data['dt'], is_group=False)
                lesson.trainer.add(*trainer)
                lesson.save()
                for student in form.cleaned_data['student']:
                    participant = Participant.objects.create(lesson=lesson, student=student)
                    pk_group = participant.student.group.pk
                messages.success(request, 'Занятие добавлено!')
                return redirect('group_schedule', pk=pk, pk_group=pk_group)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error)
        else:
            students = Student.objects.filter(group__in=ClubGroup.objects.filter(club=pk))
            form = CreateIndividualLessonForm()
            form.fields['student'].queryset = Student.objects.filter(group__in=ClubGroup.objects.filter(club=club))
            form.fields['trainer'].queryset = Trainer.objects.filter(club=club)

        return render(request, 'clubs/schedule/add_indiv.html',
                      {'form': form, 'club': club, 'current_date': timezone.datetime.now()})
    else:
        return redirect('403Forbidden')


# -------------------------------------- РАСПИСАНИЕ КЛУБ(ОВ) -----------------------------
@login_required
def club_schedule(request, pk):
    if pk > 0:
        clubs = Club.objects.filter(pk=pk)
        groups = ClubGroup.objects.filter(club__in=clubs)
        lessons_group = Lesson.objects.filter(group__in=ClubGroup.objects.filter(club=clubs[0]), is_group=True)
        lessons_individuals = Lesson.objects.filter(is_group=False)
        filtered_lessons_individuals = []
        for lesson in lessons_individuals:
            for participant in lesson.participant_set.all():
                print(participant)
                if participant.student.group in groups:
                    if lesson not in filtered_lessons_individuals:
                        filtered_lessons_individuals.append(lesson)

        return render(request, 'director/club/schedule/club_schedule.html',
                      {'title': 'Расписание', 'groups': groups, 'lessons_group': lessons_group,
                       'filtered_lessons_individuals': filtered_lessons_individuals, 'clubs': clubs, 'club': clubs[0]})
    else:
        clubs = Club.objects.filter(director=request.user.director)
        groups = ClubGroup.objects.filter(club__in=clubs)
        lessons_group = Lesson.objects.filter(group__in=ClubGroup.objects.filter(club__in=clubs), is_group=True)
        lessons_individuals = Lesson.objects.filter(is_group=False)
        filtered_lessons_individuals = []
        for lesson in lessons_individuals:
            for participant in lesson.participant_set.all():
                print(participant)
                if participant.student.group in groups:
                    if lesson not in filtered_lessons_individuals:
                        filtered_lessons_individuals.append(lesson)

        return render(request, 'director/club/schedule/club_schedule.html',
                      {'title': 'Расписание', 'groups': groups, 'lessons_group': lessons_group,
                       'filtered_lessons_individuals': filtered_lessons_individuals, 'clubs': clubs,
                       'director': request.user.director})


# -------------------------------------- РАСПИСАНИЕ ГРУПП(Ы) -----------------------------
@login_required
def group_schedule(request, pk, pk_group):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        if pk_group > 0:
            groups = ClubGroup.objects.filter(pk=pk_group)
            lessons_group = Lesson.objects.filter(group__in=ClubGroup.objects.filter(club=club), is_group=True)
            lessons_individuals = Lesson.objects.filter(is_group=False)
            filtered_lessons_individuals = []
            for lesson in lessons_individuals:
                for participant in lesson.participant_set.all():
                    if participant.student.group in groups:
                        if lesson not in filtered_lessons_individuals:
                            filtered_lessons_individuals.append(lesson)

            return render(request, 'director/club/schedule/group_schedule.html',
                          {'title': 'Расписание', 'groups': groups, 'lessons_group': lessons_group,
                           'club': club, 'filtered_lessons_individuals': filtered_lessons_individuals})
        else:
            groups = ClubGroup.objects.filter(club=club)
            lessons_group = Lesson.objects.filter(group__in=ClubGroup.objects.filter(club=club), is_group=True)
            lessons_individuals = Lesson.objects.filter(is_group=False)
            filtered_lessons_individuals = []
            for lesson in lessons_individuals:
                for participant in lesson.participant_set.all():
                    if participant.student.group in groups:
                        if lesson not in filtered_lessons_individuals:
                            filtered_lessons_individuals.append(lesson)

            return render(request, 'director/club/schedule/club_schedule.html',
                          {'title': 'Расписание', 'groups': groups, 'lessons_group': lessons_group,
                           'filtered_lessons_individuals': filtered_lessons_individuals, 'club': club})
    else:
        return redirect('403Forbidden')


# -------------------------------------- РАСПИСАНИЕ. СПИСОК УЧАСТНИКОВ УРОКА.  -----------------------------
@login_required
def students_in_lesson(request, pk, pk_lesson):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        lesson = get_object_or_404(Lesson, pk=pk_lesson)
        students = Participant.objects.filter(lesson=pk_lesson)
        return render(request, 'director/club/schedule/students_list_in_lesson.html',
                      {'students': students, 'lesson': lesson, 'club': club})
    else:
        return redirect('403Forbidden')


# -------------------------------------- РАСПИСАНИЕ. СМЕНА СТАТУСА УЧАСТИЯ В УРОКЕ  -----------------------------
@login_required
def change_status_true(request, pk, pk_lesson, pk_participant):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        participant = Participant.objects.get(pk=pk_participant)
        participant.status = True
        participant.save()
        return redirect(students_in_lesson, pk=pk, pk_lesson=pk_lesson)
    else:
        return redirect('403Forbidden')


@login_required
def change_status_false(request, pk, pk_lesson, pk_participant):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        participant = Participant.objects.get(pk=pk_participant)
        participant.status = False
        participant.save()
        return redirect(students_in_lesson, pk=pk, pk_lesson=pk_lesson)
    else:
        return redirect('403Forbidden')


# -------------------------------------- РАССЫЛКА  -----------------------------
def club_mailing(request, pk):
    if request.method == 'POST':
        form = ClubMailingForm(request.POST, request.FILES)
        if form.is_valid():
            mes_data = form.cleaned_data
            try:
                img = Image.open(request.FILES['image'])
                img_path = f'media/uploads/broadcast/{create_password()}.{img.format}'
                img.save(img_path)
                mes_data['image'] = img_path
            except MultiValueDictKeyError:
                pass

            club_pk = Club.objects.get(pk=pk).pk
            recipients = [i.tgID for i in Trainer.objects.filter(club_id=club_pk) if i.tgID is not None]
            recipients += [i.tgID for i in Student.objects.filter(club_id=club_pk) if i.tgID is not None]
            # broadcast(recipients, mes_data)
            messages.success(request, 'Успешно отправлено!')
            return render(request, 'director/club/mailing/club_mailing.html', {'club': Club.objects.get(pk=pk), 'form': form})
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error)
    else:
        form = ClubMailingForm()
        return render(request, 'director/club/mailing/club_mailing.html', {'title': 'Рассылка', 'club': Club.objects.get(pk=pk), 'form': form})


@login_required(login_url='/login/')
def personal_mailing(request, rec_type, pk_rec):
    user_data, user_type = finding_user(request.user)

    recipient, rec_type_str = '', ''
    if rec_type == 1:
        recipient = Director.objects.get(pk=pk_rec)
        rec_type_str = 'директор'
    if rec_type == 2:
        recipient = Trainer.objects.get(pk=pk_rec)
        rec_type_str = 'преподаватель'
    if rec_type == 3:
        recipient = Student.objects.get(pk=pk_rec)
        rec_type_str = 'ученик'

    if request.method == 'POST':
        if user_type == 'director':
            user_type = 'директор'
        if user_type == 'trainer':
            user_type = 'тренер'
        if user_type == 'student':
            user_type = 'ученик'
        form = PersonalMailingForm(request.POST, request.FILES)
        if form.is_valid():
            mes_data = form.cleaned_data
            try:
                img = Image.open(request.FILES['image'])
                img_path = f'media/uploads/broadcast/{create_password()}.{img.format}'
                img.save(img_path)
                mes_data['image'] = img_path
            except MultiValueDictKeyError:
                pass
            # broadcast([recipient.tgID, ], mes_data)
            messages.success(request, 'Успешно отправлено!')
            return render(request, 'director/club/mailing/personal_mailing.html',
                          {'title': 'Личное сообщение', 'form': form, 'recipient': recipient, 'rec_type': rec_type_str})
    else:
        form = PersonalMailingForm()
        return render(request, 'director/club/mailing/personal_mailing.html',
                      {'title': 'Личное сообщение', 'form': form, 'recipient': recipient, 'rec_type': rec_type_str, f'{user_type}': user_data})


# -------------------------------------- ВКЛАД В БУДУЩЕЕ  -----------------------------
def donat(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, 'director/club/investing.html',
                      {'title': 'Вклад в будущее', 'club': club})
    else:
        return redirect('403Forbidden')


# -------------------------------------- МЕРОПРИЯТИЯ  -----------------------------
def events(request, pk):
    if pk > 0:
        club = Club.objects.select_related('director').get(pk=pk)
        if request.user.director == club.director:
            return render(request, 'director/club/events.html',
                          {'title': 'Мероприятия', 'club': club})
        else:
            return redirect('403Forbidden')

    return render(request, 'director/club/events.html',
                  {'title': 'Мероприятия', 'director': request.user.director})