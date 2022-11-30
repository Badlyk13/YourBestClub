from django.db import models


# Create your models here.

class Service(models.Model):
    EVERY_DAY = 'D'
    EVERY_WEEK = 'W'
    EVERY_MONTH = 'M'
    EVERY_QUART = 'Q'
    EVERY_YEAR = 'Y'
    PERIODICITY = (
        (EVERY_DAY, 'Ежедневно'),
        (EVERY_WEEK, 'Еженедельно'),
        (EVERY_WEEK, 'Ежемесячно'),
        (EVERY_WEEK, 'Ежеквартально'),
        (EVERY_YEAR, 'Ежегодно'),
    )

    title = models.CharField(max_length=150, verbose_name='Название')
    description = models.CharField(max_length=1000, verbose_name='Описание', blank=True)
    cost = models.IntegerField(verbose_name='Стоимость')
    periodicity = models.CharField(verbose_name='Периодичность', max_length=1, choices=PERIODICITY)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Услуга(у)'
        verbose_name_plural = 'Услуги'
        ordering = ['id']
