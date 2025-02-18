from django.core.files.storage import default_storage
from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import (
    ChangePasswordSerializer,
    UserAvatarSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from users.models import Subscription, User


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user_data = UserSerializer(user, context={'request': request}).data
        return Response(user_data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action == 'update_avatar':
            return UserAvatarSerializer
        return self.serializer_class

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        user = request.user

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(user=user, author=author)

            serializer = UserSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(
            Subscription, user=user, author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        subscriptions = (
            User.objects.filter(subscriptions__user=request.user)
            .annotate(recipes_count=Count('recipes'))
            .prefetch_related('recipes')
            .order_by('id')
        )
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Пароль успешно изменен'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        methods=['get', 'put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'GET':
            serializer = UserAvatarSerializer(user)
            return Response(serializer.data)

        if request.method == 'DELETE':
            if user.avatar and user.avatar.name != 'users/avatars/default.png':
                default_storage.delete(user.avatar.name)
                user.avatar = 'users/avatars/default.png'
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = UserAvatarSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(
            raise_exception=True)
        if user.avatar and user.avatar.name != 'users/avatars/default.png':
            default_storage.delete(user.avatar.name)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.tokens.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
