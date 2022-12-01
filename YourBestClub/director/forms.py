from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import *


def clean_unique(form, field, exclude_initial=True, format="Пользователь с таким номером телефона уже существует"):
    value = form.cleaned_data.get(field)
    if value:
        qs = form._meta.model._default_manager.filter(**{field:value})
        if exclude_initial and form.initial:
            initial_value = form.initial.get(field)
            qs = qs.exclude(**{field:initial_value})
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
        fields = ['surname', 'name', 'soname', 'phone', 'avatar']

    def clean_phone(self):
        return clean_unique(self, 'phone')


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['surname', 'name', 'soname', 'avatar', 'birthday', 'agent_name', 'agent_phone']

    def clean_phone(self):
        return clean_unique(self, 'agent_phone')


class CreateClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['city', 'address', 'title', 'description', 'avatar']