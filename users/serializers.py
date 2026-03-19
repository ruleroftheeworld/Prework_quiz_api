from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email", "username", "full_name", "password", "password2",
            "level", "stream",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    average_score = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "full_name", "role",
            "level", "stream", "total_score", "quizzes_taken",
            "average_score", "date_joined", "last_seen",
        ]
        read_only_fields = ["id", "email", "role", "total_score", "quizzes_taken", "date_joined", "last_seen"]


class UserAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admin use."""
    average_score = serializers.FloatField(read_only=True)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "full_name", "role",
            "level", "stream", "is_active", "is_approved", "total_score",
            "quizzes_taken", "average_score", "date_joined", "last_seen",
            "password",
        ]
        read_only_fields = ["id", "date_joined"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserProfileSerializer(self.user).data
        return data
