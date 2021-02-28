from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import generic

from . import parser
# Create your views here.


def get_settings(request):
    return render(request, 'TableApp/index.html', {
     })
