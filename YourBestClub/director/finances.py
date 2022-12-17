from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from director.forms import FilterFinDetailsForm
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

