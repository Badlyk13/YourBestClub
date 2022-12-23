from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from director.forms import FilterFinDetailsForm, WithdrawalForm, AddPersonalPaymentForm
from director.models import Payment, Club


def fin_clubs(request, pk):
    try:
        user = request.user.director
    except:
        return redirect('403Forbidden')

    if user:
        if pk == 0:
            incoming = Payment.objects.filter(club__in=user.club_set.all(), amount__gt=0, is_personal=False).aggregate(Sum('amount'))['amount__sum']
            expenses = Payment.objects.filter(club__in=user.club_set.all(), amount__lt=0, is_personal=False).aggregate(Sum('amount'))['amount__sum']
            personal = Payment.objects.filter(club__in=user.club_set.all(), amount__lt=0, is_personal=True).aggregate(Sum('amount'))['amount__sum']
            incoming = incoming if incoming is not None else 0
            expenses = expenses if expenses is not None else 0
            personal = personal if personal is not None else 0
            return render(request, 'director/finances/club.html', {'title': 'Финансы', 'director': request.user.director,
                                                                   'incoming': incoming,
                                                                   'expenses': expenses,
                                                                   'personal': personal,
                                                                   'total': incoming + expenses + personal})
        else:
            club = Club.objects.select_related('director').get(pk=pk)
            incoming = Payment.objects.filter(club=club, amount__gt=0, is_personal=False).aggregate(Sum('amount'))['amount__sum']
            expenses = Payment.objects.filter(club=club, amount__lt=0, is_personal=False).aggregate(Sum('amount'))['amount__sum']
            personal = Payment.objects.filter(club=club, amount__lt=0, is_personal=True).aggregate(Sum('amount'))['amount__sum']
            incoming = incoming if incoming is not None else 0
            expenses = expenses if expenses is not None else 0
            personal = personal if personal is not None else 0
            return render(request, 'director/finances/club.html', {'title': 'Финансы', 'club': club,
                                                                   'incoming': incoming,
                                                                   'expenses': expenses,
                                                                   'personal': personal,
                                                                   'total': incoming + expenses + personal})


def fin_details(request, pk, type):
    try:
        user = request.user.director
    except:
        return redirect('403Forbidden')

    if user:
        today = timezone.datetime.strftime(timezone.now(), "%Y-%m-%d")
        start_date = f'{timezone.now().year}-01-01'
        payments, _type = '', ''
        if request.method == 'POST':
            form = FilterFinDetailsForm(request.POST)
            if form.is_valid():
                start_date = form.cleaned_data.get('start')
                end_date = form.cleaned_data.get('end')
                if type == 'incoming':
                    _type = 'Доходы'
                    payments = Payment.objects.filter(club__in=user.club_set.all(), amount__gt=0, is_personal=False,
                                                      created_at__range=(start_date, end_date))
                if type == 'expenses':
                    _type = 'Расходы'
                    payments = Payment.objects.filter(club__in=user.club_set.all(), amount__lt=0, is_personal=False,
                                                      created_at__range=(start_date, end_date))
                if type == 'personal':
                    _type = 'Личные'
                    payments = Payment.objects.filter(club__in=user.club_set.all(), amount__lt=0, is_personal=True,
                                                      created_at__range=(start_date, end_date))

            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    print(error)
                    messages.error(request, error)

        if request.method == 'GET':
            form = FilterFinDetailsForm()
            if pk > 0:
                club = Club.objects.select_related('director').get(pk=pk)
                if type == 'incoming':
                    _type = 'Доходы'
                    payments = Payment.objects.filter(club=club, amount__gt=0, is_personal=False)
                if type == 'expenses':
                    _type = 'Расходы'
                    payments = Payment.objects.filter(club=club, amount__lt=0, is_personal=False)
                if type == 'personal':
                    _type = 'Личные'
                    payments = Payment.objects.filter(club=club, amount__lt=0, is_personal=True)
                return render(request, 'director/finances/f_club_detail.html', {'title': f'Детализация финансов',
                                                                                'club': club, 'type': _type,
                                                                                'payments': payments, 'form': form,
                                                                                'today': today, 'start_date': start_date})
            else:
                if type == 'incoming':
                    _type = 'Доходы'
                    payments = Payment.objects.filter(club__in=user.club_set.all(), amount__gt=0, is_personal=False)
                if type == 'expenses':
                    _type = 'Расходы'
                    payments = Payment.objects.filter(club__in=user.club_set.all(), amount__lt=0, is_personal=False)
                if type == 'personal':
                    _type = 'Личные'
                    payments = Payment.objects.filter(club__in=user.club_set.all(), amount__lt=0, is_personal=True)
        form = FilterFinDetailsForm()
        return render(request, 'director/finances/f_club_detail.html', {'title': f'Детализация финансов',
                                                                        'director': request.user.director,
                                                                        'payments': payments, 'form': form,
                                                                        'today': today, 'start_date': start_date,
                                                                        'type': _type})


def withdrawal(request):
    try:
        user = request.user.director
    except:
        return redirect('403Forbidden')

    if user:
        if request.method == 'POST':
            form = WithdrawalForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data.get('amount')
                card = form.cleaned_data.get('card')
                payment = Payment.objects.create(amount=-amount, user=request.user, assignment='Вывод')
                # отправка в бот Юрию
                # broadcast([recipient.tgID, ], mes_data)
                messages.success(request, f'Заявка на вывод {amount}₽ успешно оформлена!')
                return redirect('detail', pk=user.pk)
            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error)
        else:
            form = WithdrawalForm()
            history = Payment.objects.filter(user=request.user, assignment='Вывод')
            balance = Payment.objects.filter(user=request.user, is_personal=False).aggregate(Sum('amount'))['amount__sum']
            return render(request, 'director/finances/withdrawal.html', {'title': 'Вывод средств',
                                                                         'director': request.user.director,
                                                                         'balance': balance,
                                                                         'form': form, 'history': history})


def refill(request):
    try:
        user = request.user.director
    except:
        return redirect('403Forbidden')
    if user:
        return render(request, 'director/finances/refill.html',
                      {'title': 'Пополнение баланса', 'director': user})
    else:
        return redirect('403Forbidden')


def add_personal_payment(request, pk):
    try:
        user = request.user.director
    except:
        return redirect('403Forbidden')

    if user:
        if request.method == 'POST':
            form = AddPersonalPaymentForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data.get('amount')
                assignment = form.cleaned_data.get('assignment')
                if pk > 0:
                    club = Club.objects.get(pk=pk)
                    payment = Payment.objects.create(amount=-amount, user=request.user, assignment=assignment,
                                                     is_personal=True, club=club)
                    messages.success(request, f'Личные расходы добавлены!')
                    return redirect('fin_clubs', pk=pk)
                else:
                    payment = Payment.objects.create(amount=-amount, user=request.user, assignment=assignment,
                                                     is_personal=True)
                    messages.success(request, f'Личные расходы добавлены!')
                    return redirect('fin_clubs', pk=0)

            else:
                for field in form.errors:
                    error = form.errors[field].as_text()
                    messages.error(request, error)
        else:
            form = AddPersonalPaymentForm()
            if pk > 0:
                club = Club.objects.get(pk=pk)
                history = Payment.objects.filter(user=request.user, is_personal=True, club__pk=pk)
                return render(request, 'director/finances/add_personal_payment.html', {'title': 'Добавить расходы клуба',
                                                                                       'club': club,
                                                                                       'history': history,
                                                                                       'form': form})
            else:
                history = Payment.objects.filter(user=request.user, is_personal=True)
                return render(request, 'director/finances/add_personal_payment.html', {'title': 'Добавить личные расходы',
                                                                                       'director': request.user.director,
                                                                                       'history': history,
                                                                                       'form': form})
    else:
        return redirect('403Forbidden')
