from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer

from recipes.fields import Base64ImageField
from recipes.models import Recipe
from users.models import Subscription

MAX_AVATAR_SIZE = 2 * 1024 * 1024
User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return value

    def create(self, validated_data):
        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)

        if not email:
            raise serializers.ValidationError({
                'email': 'Email обязателен для регистрации.'
            })

        if not password:
            raise serializers.ValidationError({
                'password': 'Пароль обязателен для регистрации.'
            })

        user = User(email=email, **validated_data)
        user.set_password(password)
        user.save()

        return user


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    'Неверный email или пароль',
                    code='authorization',
                )
        else:
            raise serializers.ValidationError(
                'Email и пароль обязательны',
                code='authorization',
            )

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=True,
        write_only=True,
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
    )

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Неверный текущий пароль'
            )
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data['new_password'])
        user.save()
        return user


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        if value and value.size > MAX_AVATAR_SIZE:  # 2MB
            raise serializers.ValidationError(
                'Размер изображения не должен превышать 2MB'
            )
        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        user = self.context['request'].user
        author = attrs.get('author')

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )

        return attrs
