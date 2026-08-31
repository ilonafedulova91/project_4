from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("recipients/", views.RecipientListView.as_view(), name="recipient_list"),
    path(
        "recipients/<int:pk>/",
        views.RecipientDetailView.as_view(),
        name="recipient_detail",
    ),
    path(
        "recipients/create/",
        views.RecipientCreateView.as_view(),
        name="recipient_create",
    ),
    path(
        "recipient/<int:pk>/edit/",
        views.RecipientUpdateView.as_view(),
        name="recipient_update",
    ),
    path(
        "recipient/<int:pk>/delete/",
        views.RecipientDeleteView.as_view(),
        name="recipient_delete_confirm",
    ),
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path(
        "messages/<int:pk>/", views.MessageDetailView.as_view(), name="message_detail"
    ),
    path("messages/create/", views.MessageCreateView.as_view(), name="message_create"),
    path(
        "messages/<int:pk>/edit/",
        views.MessageUpdateView.as_view(),
        name="message_update",
    ),
    path(
        "messages/<int:pk>/delete/",
        views.MessageDeleteView.as_view(),
        name="message_delete_confirm",
    ),
    path("mailings/", views.MailingListView.as_view(), name="mailing_list"),
    path(
        "mailings/<int:pk>/", views.MailingDetailView.as_view(), name="mailing_detail"
    ),
    path("mailings/create/", views.MailingCreateView.as_view(), name="mailing_create"),
    path(
        "mailings/<int:pk>/edit/",
        views.MailingUpdateView.as_view(),
        name="mailing_update",
    ),
    path(
        "mailings/<int:pk>/delete/",
        views.MailingDeleteView.as_view(),
        name="mailing_delete_confirm",
    ),
    path("mailing/<int:pk>/send/", views.send_mailing_view, name="send_mailing"),
    path("register/", views.register, name="register"),
    path("verification_sent/", views.verification_sent, name="verification_sent"),
    path("verify/<uuid:token>/", views.verify_email, name="verify_email"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="mailing/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="mailing/password_reset.html",
            email_template_name="mailing/password_reset_email.html",
            subject_template_name="mailing/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="mailing/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="mailing/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="mailing/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "manager/recipients/",
        views.ManagerRecipientListView.as_view(),
        name="manager_recipient_list",
    ),
    path(
        "manager/mailings/",
        views.ManagerMailingListView.as_view(),
        name="manager_mailing_list",
    ),
    path(
        "manager/users/", views.ManagerUserListView.as_view(), name="manager_user_list"
    ),
    path(
        "manager/users/<int:pk>/block/",
        views.manager_block_user,
        name="manager_block_user",
    ),
    path(
        "manager/mailings/<int:pk>/disable/",
        views.manager_disable_mailing,
        name="manager_disable_mailing",
    ),
    path(
        "manager/recipients/<int:pk>/",
        views.ManagerRecipientDetailView.as_view(),
        name="manager_recipient_detail",
    ),
    path(
        "manager/mailings/<int:pk>/",
        views.ManagerMailingDetailView.as_view(),
        name="manager_mailing_detail",
    ),
    path("public/", views.public_page, name="public_page"),
]
