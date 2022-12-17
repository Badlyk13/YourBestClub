import csv

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from calendar import monthrange

from director.models import ClubGroup, Club, Payment, Lesson, Student, Trainer

MONTH = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль',
         'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']


def stat_home(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, 'director/statistic/base_stat.html', {'club': club})
    else:
        return redirect('403Forbidden')


# =============================== ФИНАНСЫ ===========================================
def stat_club_finances(request, pk, period):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        incoming = Payment.objects.filter(club=club, amount__gt=0, is_personal=False)
        expenses = Payment.objects.filter(club=club, amount__lt=0)
        data_title, data_incoming_sum, data_expenses_sum = [], [], []
        if period == 0:
            min_year = incoming.order_by('created_at')[0].created_at.year
            year = min_year
            while year <= timezone.now().year:
                incoming_sum = incoming.filter(created_at__year=year).aggregate(Sum('amount'))['amount__sum']
                expenses_sum = expenses.filter(created_at__year=year).aggregate(Sum('amount'))['amount__sum']
                if incoming_sum is None and expenses_sum is None:
                    continue
                incoming_sum = incoming_sum if incoming_sum is not None else 0
                expenses_sum = expenses_sum if expenses_sum is not None else 0

                data_title.append(year)
                data_incoming_sum.append(incoming_sum)
                data_expenses_sum.append(abs(expenses_sum))
                year += 1

        if period > 2000:
            data_title = MONTH
            for i in range(1, 13):
                incoming_sum = incoming.filter(created_at__year=period, created_at__month=i).aggregate(Sum('amount'))[
                    'amount__sum']
                expenses_sum = expenses.filter(created_at__year=period, created_at__month=i).aggregate(Sum('amount'))[
                    'amount__sum']

                incoming_sum = incoming_sum if incoming_sum is not None else 0
                expenses_sum = expenses_sum if expenses_sum is not None else 0
                data_incoming_sum.append(incoming_sum)
                data_expenses_sum.append(abs(expenses_sum))

        return render(request, 'director/statistic/finances.html', {'title': 'Статистика', 'club': club,
                                                                    'data_title': data_title,
                                                                    'data_incoming_sum': data_incoming_sum,
                                                                    'data_expenses_sum': data_expenses_sum,
                                                                    'period': period})
    else:
        return redirect('403Forbidden')


def stat_club_finances_month(request, pk, year, month):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        incoming = Payment.objects.filter(club=club, amount__gt=0, is_personal=False)
        expenses = Payment.objects.filter(club=club, amount__lt=0)
        data_title, data_incoming_sum, data_expenses_sum = [], [], []
        days = monthrange(timezone.now().year, month)
        for i in range(1, days[1] + 1):
            incoming_sum = \
                incoming.filter(created_at__year=year, created_at__month=month, created_at__day=i).aggregate(
                    Sum('amount'))[
                    'amount__sum']
            expenses_sum = \
                expenses.filter(created_at__year=year, created_at__month=month, created_at__day=i).aggregate(
                    Sum('amount'))[
                    'amount__sum']
            incoming_sum = incoming_sum if incoming_sum is not None else 0
            expenses_sum = expenses_sum if expenses_sum is not None else 0
            data_title.append(i)
            data_incoming_sum.append(incoming_sum)
            data_expenses_sum.append(abs(expenses_sum))

        return render(request, 'director/statistic/finances.html', {'title': 'Статистика', 'club': club,
                                                                    'data_title': data_title,
                                                                    'data_incoming_sum': data_incoming_sum,
                                                                    'data_expenses_sum': data_expenses_sum,
                                                                    'year': year, 'month': MONTH[month - 1]})
    else:
        return redirect('403Forbidden')


def stat_detail(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        all_payments = Payment.objects.filter(club=club)
        print(all_payments)
        return render(request, 'director/statistic/detail.html', {'title': 'Детализация', 'club': club,
                                                                  'all_payments': all_payments})

    else:
        return redirect('403Forbidden')


def download_detail(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        # Создайте объект HttpResponse с соответствующим заголовком CSV.
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="club_{club.pk}.csv"'},
        )

        writer = csv.writer(response)
        writer.writerow(['Дата', 'Сумма', 'Пользователь', 'Назначение'])
        all_payments = Payment.objects.filter(club=club)
        user = ''
        for row in all_payments:
            try:
                user = row.user.director
            except:
                try:
                    user = row.user.trainer
                except:
                    user = row.user.student
            writer.writerow([row.created_at, row.amount, user, row.assignment])

        return response

    else:
        return redirect('403Forbidden')


# =============================== ТРЕНИРОВКИ ===========================================
def stat_lessons(request, pk, year):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        lessons = Lesson.objects.filter(group__in=ClubGroup.objects.filter(club=club))
        lessons_ind = Lesson.objects.filter(trainer__club=club, is_group=False)
        data_title, data_qty_group, data_qty_ind = [], [], []
        if year == 0:
            min_year = lessons.order_by('dt')[0].dt.year
            cur_year = min_year
            while cur_year <= timezone.now().year:
                qty_group = lessons.filter(dt__year=cur_year, is_group=True).count()
                qty_ind = lessons_ind.filter(dt__year=cur_year).count()
                print(qty_ind)
                data_title.append(cur_year)
                data_qty_group.append(qty_group)
                data_qty_ind.append(qty_ind)
                cur_year += 1

        else:
            data_title = MONTH
            for i in range(1, 13):
                qty_group = lessons.filter(dt__year=year, dt__month=i, is_group=True).count()
                qty_ind = lessons_ind.filter(dt__year=year, dt__month=i).count()
                data_qty_group.append(qty_group)
                data_qty_ind.append(qty_ind)

        return render(request, 'director/statistic/lessons.html', {'title': 'Статистика', 'club': club,
                                                                   'data_title': data_title,
                                                                   'data_qty_group': data_qty_group,
                                                                   'data_qty_ind': data_qty_ind,
                                                                   'period': year})
    else:
        return redirect('403Forbidden')


# =============================== УЧЕНИКИ ===========================================
def stat_registered_students(request, pk, year):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        students = Student.objects.filter(group__in=ClubGroup.objects.filter(club=club))
        data_title, data_qty_students, data_total, data_max_in_lesson, data_qty_leave = [], [], [], [], []
        if year == 0:
            min_year = students.order_by('registered_at')[0].registered_at.year
            cur_year = min_year
            while cur_year <= timezone.now().year:
                qty_students = students.filter(registered_at__year=cur_year).count()
                total = students.filter(registered_at__year__lte=cur_year).count()
                qty_leave = students.filter(no_active_at__year=cur_year).count()
                qty_leave_total = students.filter(no_active_at__year__lte=cur_year).count()
                data_title.append(cur_year)
                data_qty_students.append(qty_students)
                data_total.append(total-qty_leave_total)
                data_qty_leave.append(qty_leave)
                cur_year += 1

        else:
            data_title = MONTH
            for i in range(1, 13):
                qty_students = students.filter(registered_at__year=year, registered_at__month=i).count()
                total = students.filter(registered_at__year=year, registered_at__month__lte=i).count()
                qty_leave = students.filter(no_active_at__year=year, no_active_at__month=i).count()
                qty_leave_total = students.filter(no_active_at__year__lte=year, no_active_at__month__lte=i).count()
                data_qty_students.append(qty_students)
                data_total.append(total-qty_leave_total)
                data_qty_leave.append(qty_leave)

        return render(request, 'director/statistic/students_registration.html', {'title': 'Статистика', 'club': club,
                                                                                 'data_title': data_title,
                                                                                 'data_qty_students': data_qty_students,
                                                                                 'data_total': data_total,
                                                                                 'data_qty_leave': data_qty_leave,
                                                                                 'period': year})
    else:
        return redirect('403Forbidden')


# =============================== ГРУППА ===========================================
def stat_group_students(request, pk, pk_group, year):
    group = ClubGroup.objects.select_related('club').get(pk=pk_group)
    if request.user.director == group.club.director:
        students = Student.objects.filter(group__pk=pk_group)
        data_title, data_qty_students, data_total, data_max_in_lesson, data_qty_leave = [], [], [], [], []
        if year == 0:
            min_year = students.order_by('registered_at')[0].registered_at.year
            cur_year = min_year
            while cur_year <= timezone.now().year:
                qty_students = students.filter(registered_at__year=cur_year).count()
                total = students.filter(registered_at__year__lte=cur_year).count()
                qty_leave = students.filter(no_active_at__year=cur_year).count()
                qty_leave_total = students.filter(no_active_at__year__lte=cur_year).count()
                data_title.append(cur_year)
                data_qty_students.append(qty_students)
                data_total.append(total-qty_leave_total)
                data_qty_leave.append(qty_leave)
                cur_year += 1

        else:
            data_title = MONTH
            for i in range(1, 13):
                qty_students = students.filter(registered_at__year=year, registered_at__month=i).count()
                total = students.filter(registered_at__year=year, registered_at__month__lte=i).count()
                qty_leave = students.filter(no_active_at__year=year, no_active_at__month=i).count()
                qty_leave_total = students.filter(no_active_at__year__lte=year, no_active_at__month__lte=i).count()
                data_qty_students.append(qty_students)
                data_total.append(total-qty_leave_total)
                data_qty_leave.append(qty_leave)

        return render(request, 'director/statistic/group_students.html', {'title': 'Статистика', 'group': group,
                                                                                 'data_title': data_title,
                                                                                 'data_qty_students': data_qty_students,
                                                                                 'data_total': data_total,
                                                                                 'data_qty_leave': data_qty_leave,
                                                                                 'period': year})
    else:
        return redirect('403Forbidden')


# =============================== ИНДИВИДУАЛЬНЫЕ ===========================================
def stat_individuals(request, pk, year):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        lessons_ind = Lesson.objects.filter(trainer__club=club, is_group=False)
        trainers = Trainer.objects.filter(club=club, is_active=True)
        data_title, data_qty_ind, data_trainers, data_qty_lesson = [], [], [], []
        if year == 0:
            min_year = lessons_ind.order_by('dt')[0].dt.year
            cur_year = min_year
            while cur_year <= timezone.now().year:
                qty_ind = lessons_ind.filter(dt__year=cur_year).count()
                data_title.append(cur_year)
                data_qty_ind.append(qty_ind)
                cur_year += 1

            for trainer in trainers:
                data_trainers.append(trainer.surname)
                qty_lesson = lessons_ind.filter(trainer=trainer).count()
                data_qty_lesson.append(qty_lesson)

        else:
            data_title = MONTH
            for i in range(1, 13):
                qty_ind = lessons_ind.filter(dt__year=year, dt__month=i).count()
                data_qty_ind.append(qty_ind)

            for trainer in trainers:
                data_trainers.append(trainer.surname)
                qty_lesson = lessons_ind.filter(dt__year=year, trainer=trainer).count()
                data_qty_lesson.append(qty_lesson)
        return render(request, 'director/statistic/individuals.html', {'title': 'Статистика', 'club': club,
                                                                       'data_title': data_title,
                                                                       'data_qty_lesson': data_qty_lesson,
                                                                       'data_trainers': data_trainers,
                                                                       'data_qty_ind': data_qty_ind,
                                                                       'period': year})
    else:
        return redirect('403Forbidden')
