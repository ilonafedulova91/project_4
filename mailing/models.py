import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipients"
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.full_name}: {self.email}"


class Message(models.Model):
    subject = models.CharField(max_length=250)
    body = models.TextField()

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_CREATED = "Создана"
    STATUS_STARTED = "Запущена"
    STATUS_COMPLETED = "Завершена"

    STATUS_CHOICES = [
        (STATUS_CREATED, STATUS_CREATED),
        (STATUS_STARTED, STATUS_STARTED),
        (STATUS_COMPLETED, STATUS_COMPLETED),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mailings"
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_CREATED
    )
    is_active = models.BooleanField(default=True)

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="mailings"
    )
    recipients = models.ManyToManyField(Recipient, related_name="mailings")

    def clean(self):
        super().clean()

        now = timezone.now()

        if self.start_time and self.start_time < now:
            raise ValidationError(
                {"start_time": "Дата и время начала не могут быть в прошлом."}
            )

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                {"end_time": "Дата окончания должна быть позже даты начала."}
            )

    def update_status(self):
        now = timezone.now()

        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif now <= self.end_time:
            new_status = self.STATUS_STARTED
        else:
            new_status = self.STATUS_COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status"])

    def __str__(self):
        return f"Рассылка #{self.pk}: {self.message.subject}"


class MailingAttempt(models.Model):
    STATUS_SUCCESS = "Успешно"
    STATUS_FAILED = "Не успешно"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, STATUS_SUCCESS),
        (STATUS_FAILED, STATUS_FAILED),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    server_response = models.TextField(blank=True)

    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="attempts"
    )

    def __str__(self):
        return f"Попытка рассылки #{self.mailing.pk}: {self.status}"


class UserProfile(models.Model):
    ROLE_USER = "user"
    ROLE_MANAGER = "manager"

    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_MANAGER, "Manager"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    email_verified = models.BooleanField(default=False)

    verification_token = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)

    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}: {self.get_role_display()}"
