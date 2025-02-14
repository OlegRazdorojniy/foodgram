from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage

from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription, User
from users.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserAvatarSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author,
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(
            Subscription,
            user=request.user,
            author=author,
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
            User.objects.filter(following__user=request.user)
            .annotate(recipes_count=Count('recipes'))
            .prefetch_related('recipes')
            .order_by('-recipes__pub_date')
        )
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            subscriptions,
            many=True,
            context={'request': request},
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
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'detail': 'Пароль успешно изменен'},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
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
        if serializer.is_valid():
            if user.avatar and user.avatar.name != 'users/avatars/default.png':
                default_storage.delete(user.avatar.name)
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

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
def user_create(request):
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(
        data=request.data,
        context={'request': request},
    )
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
