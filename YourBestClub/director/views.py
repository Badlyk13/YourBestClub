from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from YourBestClub.settings import TELEGRAM_BOT_URI
from YourBestClub.utils import finding_user
from director.forms import UserLoginForm, UserCreateForm, DirectorForm, TrainerForm, StudentForm
from director.models import Director, Trainer, Student, ClubGroup, Club


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
                return redirect('detail', user_type='director', pk=user.director.pk)
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
                return redirect('detail', user_type='director', pk=request.user.director.pk)
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
def add_details(request, user_type, pk_group=None, pk_club=None):
    form = ''
    if request.method == 'POST':
        if user_type == 'director':
            form = DirectorForm(request.POST, request.FILES)
        if user_type == 'trainer':
            form = TrainerForm(request.POST, request.FILES)
        if user_type == 'student':
            form = StudentForm(request.POST, request.FILES)

        if form.is_valid():
            form.save(commit=False)
            form.instance.user = request.user
            if user_type == 'trainer':
                form.instance.club = Club.objects.get(pk=pk_club)
            if user_type == 'student':
                form.instance.group = ClubGroup.objects.get(pk=pk_group)
            reg_user = form.save()
            messages.success(request, 'Шаг 2 успешно пройден! Последний шаг...')
            return redirect('detail', user_type=user_type, pk=reg_user.pk)
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error + ' ' + field)
    else:
        if user_type == 'director':
            form = DirectorForm()
        if user_type == 'trainer':
            form = TrainerForm()
        if user_type == 'student':
            form = StudentForm()
            form.fields['group'].queryset = ClubGroup.objects.filter(pk=pk_group)
        return render(request, f'director/{user_type}/add.html',
                      {'title': 'Шаг 2. Личные данные', 'form': form})


@login_required
def edit_details(request, user_type, pk):
    form, user_data = '', ''
    if request.method == 'POST':
        if user_type == 'director':
            form = DirectorForm(request.POST, request.FILES, instance=Director.objects.get(pk=pk))
        if user_type == 'trainer':
            form = TrainerForm(request.POST, request.FILES, instance=Trainer.objects.get(pk=pk))
        if user_type == 'student':
            form = StudentForm(request.POST, request.FILES, instance=Student.objects.get(pk=pk))

        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения внесены!')
            return redirect('detail', user_type=user_type, pk=pk)
        else:
            for field in form.errors:
                error = form.errors[field].as_text()
                messages.error(request, error + ' ' + field)
    else:
        if user_type == 'director':
            form = DirectorForm(instance=Director.objects.get(pk=pk))
            user_data = Director.objects.get(pk=pk)
        if user_type == 'trainer':
            form = TrainerForm(instance=Trainer.objects.get(pk=pk))
            user_data = Trainer.objects.get(pk=pk)
        if user_type == 'student':
            form = StudentForm(instance=Student.objects.get(pk=pk))
            user_data = Student.objects.get(pk=pk)
        return render(request, f'director/{user_type}/edit.html',
                      {'title': 'Личные данные', 'form': form, f'{user_type}': user_data})


@login_required
def detail(request, user_type, pk):
    user_data, user_type = finding_user(request.user)
    link = f"{TELEGRAM_BOT_URI}c{pk}{user_type[0]}"
    return render(request, f'director/{user_type}/detail.html',
                  {'title': 'Личный кабинет', f'{user_type}': user_data, 'link': link})


@login_required
def delete(request, user_type, pk):
    user_data, user_type = finding_user(request.user)
    return render(request, f'director/registration/delete.html',
                  {'title': 'Удаление', 'user_data': user_data, 'user_type': user_type})


@login_required
def delete_confirm(request, user_type, pk):
    user = request.user
    user.delete()
    return redirect('login')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Пароль обновлен!')
            return redirect('office')
        else:
            for field in form.errors:
                messages.error(request, form.errors[field].as_text())
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'director/registration/change_password.html', {'title': 'Изменение пароля', 'form': form, })


@login_required
def set_password(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('office')
    else:
        form = SetPasswordForm(request.user)
        return render(request, 'director/registration/set_password.html', {'title': 'Создание пароля', 'form': form})


