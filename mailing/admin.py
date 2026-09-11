from django.contrib import admin

from .models import Mailing, MailingAttempt, Message, Recipient, UserProfile


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "comment")
    search_fields = ("email", "full_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "body")
    search_fields = ("subject",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "start_time", "end_time", "status", "message")
    list_filter = ("status",)
    filter_horizontal = ("recipients",)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "mailing", "attempt_time", "status", "server_response")
    list_filter = ("status", "attempt_time")
    search_fields = ("mailing__id", "server_response")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email_verified", "role", "is_blocked")
    list_filter = ("email_verified", "is_blocked")
    search_fields = ("user__username", "user__email")
