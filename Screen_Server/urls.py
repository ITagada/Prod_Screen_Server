from django.urls import path

from Screen_Server import views

# URL-маршруты для приложения Screen_Server.
# Каждый путь связан с соответствующим view-функцией из файла views.py.
urlpatterns = [
    path('', views.index, name='index'),
# Главная страница, инициализирует определение модуля по UDP-пакету.
    path('BNT/', views.get_BNT, name='BNT'),
# Заглушка или альтернативный маршрут для BNT-режима (если реализован).
    path('moscowBNT/', views.moscowBNT, name='moscowBNT'),
# Основной интерфейс отображения данных по модулю Moscow.
    path('get_module_state/', views.get_module_state, name='get_module_state'),
# Возвращает текущий активный модуль (например, 'moscow') через JSON.
]

