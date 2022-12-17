from django.shortcuts import render

from director.models import Club
from services.models import Service


# Create your views here.
def all_services(request, pk):
    club = Club.objects.select_related('director').get(pk=pk)
    if request.user.director == club.director:
        return render(request, 'services/list.html', {'title': 'Услуги', 'club': club, 'all_services': Service.objects.all()})

