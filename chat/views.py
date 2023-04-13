from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models


from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from asgiref.sync import sync_to_async
from tortoise import Tortoise
from django.conf import settings


from django.shortcuts import render, redirect
from .models import ChatGroup
from .tortoise_models import ChatMessage


User = get_user_model()


class ChatMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'chat_group',)


@login_required
def create_chat(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        chat_group = ChatGroup.objects.create(name=name, description=description)
        chat_group.user_set.add(request.user)
        chat_group.save()
        # перенаправляем пользователя в созданный чат
        return redirect(reverse('chat:room', args=[chat_group.id]))
    else:
        return render(request, 'chat/create_chat.html')


@login_required
def add_users_to_group(request, group_id):
    if request.method == 'POST':
        usernames = request.POST.getlist('users')

        # Получаем чат-группу по ее идентификатору
        group = ChatGroup.objects.get(id=group_id)

        # Получаем список пользователей из базы данных
        users = User.objects.filter(username__in=usernames)

        # Добавляем пользователей в группу
        group.user_set.add(*users)

        # Перенаправляем пользователя на страницу чата
        return HttpResponseRedirect(reverse('chat:room', args=(group_id,)))

    # Если метод GET, то отображаем форму добавления пользователей
    users = User.objects.exclude(groups__id=group_id)
    return render(request, 'chat/add_users.html', {'users': users, 'group_id': group_id})


@login_required
def index(request):
    return render(request, 'chat/index.html', {})


def get_participants(group_id=None, group_obj=None, user=None):
    """ function to get all participants that belong the specific group """

    if group_id:
        chatgroup = ChatGroup.objects.get(id=id)
    else:
        chatgroup = group_obj

    temp_participants = []
    for participants in chatgroup.user_set.values_list('username', flat=True):
        if participants != user:
            temp_participants.append(participants.title())
    temp_participants.append('You')
    return ', '.join(temp_participants)


@login_required
def room(request, group_id):
    if request.user.groups.filter(id=group_id).exists():
        chatgroup = ChatGroup.objects.get(id=group_id)
        # TODO: make sure user assigned to existing group
        assigned_groups = list(request.user.groups.values_list('id', flat=True))
        groups_participated = ChatGroup.objects.filter(id__in=assigned_groups)
        return render(request, 'chat/room.html', {
            'chatgroup': chatgroup,
            'participants': get_participants(group_obj=chatgroup, user=request.user.username),
            'groups_participated': groups_participated,
            'GIPHY_URL': settings.GIPHY_URL,
            'API_KEY': settings.API_KEY
        })

    else:
        return HttpResponseRedirect(reverse("chat:unauthorized"))


@login_required
def unauthorized(request):
    return render(request, 'chat/unauthorized.html', {})


async def history(request, room_id):
    await Tortoise.init(**settings.TORTOISE_INIT)

    chat_message = await ChatMessage.filter(room_id=room_id).order_by('date_created').values()
    await Tortoise.close_connections()

    return await sync_to_async(JsonResponse)(chat_message, safe=False)
