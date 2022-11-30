from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from PIL import Image

from services.models import Service


# ===========================================================================
class Director(models.Model):
    user = models.OneToOneField(User, verbose_name='User', on_delete=models.CASCADE)
    surname = models.CharField(max_length=64, blank=True, verbose_name='Фамилия')
    name = models.CharField(max_length=64, blank=True, verbose_name='Имя')
    soname = models.CharField(max_length=64, blank=True, verbose_name='Отчество')
    phone = models.CharField(max_length=16, unique=True, blank=True, verbose_name='Номер телефона')
    avatar = models.ImageField(upload_to='avatars_director/', verbose_name='Аватар', default='/no-image.png')
    tgID = models.IntegerField(unique=True, blank=True, null=True, verbose_name='Телеграм')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    def __str__(self):
        return f'{self.surname} {self.name} {self.soname}'

    def save(self, *args, **kwargs):
        super(Director, self).save(*args, **kwargs)
        try:
            filepath = self.avatar.path
            img = Image.open(filepath)
            if img.width > img.height:
                dist = int((img.width - img.height) / 2)
                cropped = img.crop((dist, 0, img.width - dist, img.height))
            else:
                dist = int((img.height - img.width) / 2)
                cropped = img.crop((0, dist, img.width, img.height - dist))
            cropped.save(filepath)
        except:
            pass

    def get_absolute_url(self):
        return reverse('director_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Директор(а)'
        verbose_name_plural = 'Директора'
        ordering = ['surname']


# ===========================================================================
class Club(models.Model):
    city = models.CharField(max_length=100, verbose_name='Город')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    title = models.CharField(max_length=100, verbose_name='Название')
    description = models.CharField(max_length=300, verbose_name='Описание', blank=True)
    avatar = models.ImageField(upload_to='clubs_logo/', default='/no-image.png', verbose_name='Логотип')
    director = models.ForeignKey(Director, on_delete=models.CASCADE, verbose_name='Директор')
    services = models.ManyToManyField(Service, blank=True, verbose_name='Услуги')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return f'{self.title}, {self.city}'

    def save(self, *args, **kwargs):
        super(Club, self).save(*args, **kwargs)
        try:
            filepath = self.avatar.path
            img = Image.open(filepath)
            if img.width > img.height:
                dist = int((img.width - img.height) / 2)
                cropped = img.crop((dist, 0, img.width - dist, img.height))
            else:
                dist = int((img.height - img.width) / 2)
                cropped = img.crop((0, dist, img.width, img.height - dist))
            cropped.save(filepath)
        except:
            pass

    def get_absolute_url(self):
        return reverse('club_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Клуб'
        verbose_name_plural = 'Клубы'
        ordering = ['title']
        unique_together = (('title', 'city'),)


# ===========================================================================
class ClubSubscription(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, verbose_name='Клуб')
    title = models.CharField(max_length=100, verbose_name='Название')
    qty_lesson = models.IntegerField(verbose_name='Количество занятий')
    cost = models.IntegerField(verbose_name='Стоимость')

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'
        ordering = ['id']
        unique_together = (('qty_lesson', 'cost'),)


# ===========================================================================
class ClubGroup(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, verbose_name='Клуб')
    title = models.CharField(max_length=100, verbose_name='Название')
    description = models.CharField(max_length=300, verbose_name='Описание', blank=True)
    lesson_price = models.IntegerField(verbose_name='Стоимость занятия')
    notification = models.IntegerField(verbose_name='Оповещение', default=180)
    subscription = models.ManyToManyField(ClubSubscription, blank=True, verbose_name='Абонементы')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    def __str__(self):
        return f'{self.title}'

    def get_absolute_url(self):
        return reverse('group_list', kwargs={'pk': self.club.pk})

    class Meta:
        verbose_name = 'Группа(у)'
        verbose_name_plural = 'Группы'
        ordering = ['id']
        unique_together = (('title', 'club'),)


# ===========================================================================
class Trainer(models.Model):
    user = models.OneToOneField(User, verbose_name='User', on_delete=models.CASCADE, null=True)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, verbose_name='Клуб', null=True)
    surname = models.CharField(max_length=64, verbose_name='Фамилия')
    name = models.CharField(max_length=64, verbose_name='Имя')
    soname = models.CharField(max_length=64, verbose_name='Отчество')
    phone = models.CharField(unique=True, max_length=16, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='avatars_trainer/', verbose_name='Аватар', default='/no-image.png')
    wage = models.IntegerField(verbose_name='Оклад', null=True, blank=True)
    cost = models.IntegerField(verbose_name='Ставка за групповое занятие', null=True, blank=True)
    cost_individual = models.IntegerField(verbose_name='Ставка за индивидуальное занятие', null=True, blank=True)
    cost_for_student = models.IntegerField(verbose_name='Стоимость индив. для студента', null=True, blank=True)
    tgID = models.IntegerField(unique=True, verbose_name='Телеграм', blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return f'{self.surname} {self.name} {self.soname}'

    def get_absolute_url(self):
        return reverse('trainer_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        super(Trainer, self).save(*args, **kwargs)
        try:
            filepath = self.avatar.path
            img = Image.open(filepath)
            if img.width > img.height:
                dist = int((img.width - img.height) / 2)
                cropped = img.crop((dist, 0, img.width - dist, img.height))
            else:
                dist = int((img.height - img.width) / 2)
                cropped = img.crop((0, dist, img.width, img.height - dist))
            cropped.save(filepath)
        except:
            pass

    class Meta:
        verbose_name = 'Тренер(а)'
        verbose_name_plural = 'Тренера'
        ordering = ['surname']


# ===========================================================================
class Student(models.Model):
    user = models.OneToOneField(User, verbose_name='User', on_delete=models.CASCADE, null=True)
    group = models.ForeignKey(ClubGroup, on_delete=models.CASCADE, verbose_name='Группа')
    surname = models.CharField(max_length=64, verbose_name='Фамилия')
    name = models.CharField(max_length=64, verbose_name='Имя')
    soname = models.CharField(max_length=64, verbose_name='Отчество', blank=True)
    avatar = models.ImageField(upload_to='avatars_student/', verbose_name='Аватар', default='/no-image.png')
    birthday = models.DateField(verbose_name='Дата рождения')
    agent_name = models.CharField(max_length=128, verbose_name='Имя представителя')
    agent_phone = models.CharField(max_length=16, verbose_name='Телефон представителя')
    tgID = models.IntegerField(unique=True, blank=True, null=True, verbose_name='Телеграм')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return f'{self.surname} {self.name} {self.soname}'

    def get_absolute_url(self):
        return reverse('student_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        super(Student, self).save(*args, **kwargs)
        try:
            filepath = self.avatar.path
            img = Image.open(filepath)
            if img.width > img.height:
                dist = int((img.width - img.height) / 2)
                cropped = img.crop((dist, 0, img.width - dist, img.height))
            else:
                dist = int((img.height - img.width) / 2)
                cropped = img.crop((0, dist, img.width, img.height - dist))
            cropped.save(filepath)
        except:
            pass
        lessons = Lesson.objects.filter(is_group=True, group=self.group)
        if lessons:
            for lesson in lessons:
                participant = Participant.objects.create(lesson=lesson, student=self)

    class Meta:
        verbose_name = 'Ученик(а)'
        verbose_name_plural = 'Ученики'
        ordering = ['surname']
        unique_together = (('surname', 'name', 'soname', 'agent_phone'),)


# ===========================================================================
class Lesson(models.Model):
    dt = models.DateTimeField(verbose_name='Дата/время')
    is_group = models.BooleanField(verbose_name='Групповое', default=True)
    group = models.ForeignKey(ClubGroup, null=True, blank=True, on_delete=models.CASCADE, verbose_name='Группа')
    trainer = models.ManyToManyField(Trainer, blank=True, verbose_name='Тренер(а)')

    def __str__(self):
        return f'{self.dt} | {self.is_group} | {self.group}'

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['dt']

    def save(self, *args, **kwargs):
        super(Lesson, self).save(*args, **kwargs)
        if self.is_group:
            students = Student.objects.filter(group=self.group)
            for student in students:
                participant = Participant.objects.create(lesson=self, student=student)


# ===========================================================================
class Participant(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Группа')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='Ученик')
    status = models.BooleanField(verbose_name='Статус', default=True)

    def __str__(self):
        return f'{self.lesson} | {self.student} | {self.status}'

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'
        ordering = ['lesson']

