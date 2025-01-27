from django.urls import path

from Screen_Server import views

urlpatterns = [
    path('', views.index),
    path('BNT/', views.get_BNT, name='BNT'),
    path('start-server/', views.start_udp_server),
]