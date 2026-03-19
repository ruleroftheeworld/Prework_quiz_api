from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"
        TEACHER = "teacher", "Teacher" 

    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Stream(models.TextChoices):
        COMPUTER_SCIENCE = "computer_science", "Computer Science"
        NON_TECHNICAL = "non_technical", "Non Technical"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    stream = models.CharField(max_length=30, choices=Stream.choices, default=Stream.COMPUTER_SCIENCE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(null=True, blank=True)

    is_approved = models.BooleanField(default=False,
    help_text="Teachers must be approved by admin before creating tests")

    # Aggregate score stored at registration / updated on each quiz
    total_score = models.FloatField(default=0.0)
    quizzes_taken = models.PositiveIntegerField(default=0)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def average_score(self):
        if self.quizzes_taken == 0:
            return 0.0
        return round(self.total_score / self.quizzes_taken, 2)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_approved_teacher(self):
        return self.role == self.Role.TEACHER and self.is_approved
