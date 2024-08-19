from django.urls import path

from Screen_Server import views

urlpatterns = [
    path('', views.index),
]