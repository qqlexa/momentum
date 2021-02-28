from django.urls import path

from . import views

app_name = 'TableApp'
urlpatterns = [
    path('', views.get_settings, name='index'),\
]
