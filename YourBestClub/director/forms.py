from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import *


def clean_unique(form, field, exclude_initial=True, format="Пользователь с таким номером телефона уже существует"):
    value = form.cleaned_data.get(field)
    if value:
        qs = form._meta.model._default_manager.filter(**{field: value})
        if exclude_initial and form.initial:
            initial_value = form.initial.get(field)
            qs = qs.exclude(**{field: initial_value})
        if qs.count() > 0:
            raise forms.ValidationError(format)
    return value


class UserCreateForm(UserCreationForm):
    username = forms.CharField(label='Логин', max_length=50)
    password1 = forms.CharField(label="Пароль")
    password2 = forms.CharField(label="Повторите пароль")

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class DirectorForm(forms.ModelForm):
    class Meta:
        model = Director
        fields = ['surname', 'name', 'soname', 'phone', 'avatar']

    def clean_phone(self):
        return clean_unique(self, 'phone')


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['surname', 'name', 'soname', 'phone', 'avatar', 'cost', 'cost_for_student', 'cost_individual', 'wage']

    def clean_phone(self):
        return clean_unique(self, 'phone')


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['surname', 'name', 'soname', 'avatar', 'birthday', 'agent_name', 'agent_phone', 'group', 'is_active']

    def clean_phone(self):
        return clean_unique(self, 'agent_phone')


class CreateClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['city', 'address', 'title', 'description', 'avatar']


class CreateSubscriptionForm(forms.ModelForm):
    class Meta:
        model = ClubSubscription
        fields = ['title', 'qty_lesson', 'cost']


class CreateGroupForm(forms.ModelForm):
    class Meta:
        model = ClubGroup
        fields = ['title', 'description', 'lesson_price', 'notification', 'subscription', 'avatar']


class CreateLessonForm(forms.Form):
    dt = forms.DateTimeField(label='Дата, время', localize=True)
    group = forms.ModelChoiceField(queryset=ClubGroup.objects.all(), label='Группа', blank=True)
    trainer = forms.ModelMultipleChoiceField(queryset=Trainer.objects.all(), label='Тренер')
    qty_weeks = forms.IntegerField(label='Количество недель')


class CreateIndividualLessonForm(forms.Form):
    dt = forms.DateTimeField(label='Дата, время', localize=True)
    student = forms.ModelMultipleChoiceField(queryset=Student.objects.all(), label='Ученик(и)')
    trainer = forms.ModelMultipleChoiceField(queryset=Trainer.objects.all(), label='Тренер')


class ClubMailingForm(forms.Form):
    CHOICES = (
        ('ALL', 'Всем'),
        ('TR', 'Тренера'),
        ('ST', 'Ученики'),
    )
    recipient = forms.ChoiceField(choices=CHOICES, label='Получатели')
    subject = forms.CharField(max_length=50, label='Тема')
    text = forms.CharField(max_length=1000, label='Текст')
    image = forms.ImageField(label='Изображение', required=False)


class PersonalMailingForm(forms.Form):
    subject = forms.CharField(max_length=50, label='Тема')
    text = forms.CharField(max_length=1000, label='Текст')
    image = forms.ImageField(label='Изображение', required=False)


class FilterFinDetailsForm(forms.Form):
    start = forms.DateField(label='Дата начала')
    end = forms.DateField(label='Дата окончания')


class WithdrawalForm(forms.Form):
    amount = forms.IntegerField(label='Сумма')
    card = forms.CharField(max_length=25, label='Номер карты')
