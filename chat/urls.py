from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('history/<str:room_id>/', views.history, name='history'),
    path('create_chat/', views.create_chat, name='create_chat'),
    path('<int:group_id>/add_users/', views.add_users_to_group, name='add_users_to_group'),
    path('unauthorized/', views.unauthorized, name='unauthorized'),
    path('<str:group_id>/', views.room, name='room'),
]
