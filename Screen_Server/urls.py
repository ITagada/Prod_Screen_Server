from django.urls import path

from Screen_Server import views

urlpatterns = [
    path('', views.index, name='index'),
    path('BNT/', views.get_BNT, name='BNT'),
    path('moscowBNT/', views.moscowBNT, name='moscowBNT'),
]

