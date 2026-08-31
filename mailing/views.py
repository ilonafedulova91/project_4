from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import cache_control
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import MailingForm, MessageForm, RecipientForm, RegistrationForm
from .models import Mailing, MailingAttempt, Message, Recipient, UserProfile
from .services import invalidate_home_cache, send_mailing


@cache_control(public=True, max_age=60)
def public_page(request):
    return render(request, "mailing/public_page.html")


class ManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not hasattr(request.user, "profile"):
            raise PermissionDenied

        if request.user.profile.role != UserProfile.ROLE_MANAGER:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class ManagerRecipientListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = Recipient
    template_name = "mailing/manager_recipient_list.html"
    context_object_name = "recipients"


class ManagerRecipientDetailView(LoginRequiredMixin, ManagerRequiredMixin, DetailView):
    model = Recipient
    template_name = "mailing/manager_recipient_detail.html"
    context_name = "recipient"


class RecipientListView(LoginRequiredMixin, ListView):
    model = Recipient
    template_name = "mailing/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class RecipientDetailView(LoginRequiredMixin, DetailView):
    model = Recipient
    template_name = "mailing/recipient_detail.html"
    context_object_name = "recipient"

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        invalidate_home_cache(self.request.user.pk)
        return response


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("recipient_list")

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_home_cache(self.request.user.pk)
        return response


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipient
    template_name = "mailing/recipient_delete_confirm.html"
    success_url = reverse_lazy("recipient_list")

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_home_cache(self.request.user.pk)
        return response


class MessageListView(ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages"


class MessageDetailView(DetailView):
    model = Message
    template_name = "mailing/message_detail.html"
    context_object_name = "message"


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("message_list")


class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("message_list")


class MessageDeleteView(DeleteView):
    model = Message
    template_name = "mailing/message_delete_confirm.html"
    success_url = reverse_lazy("message_list")


class ManagerMailingListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/manager_mailing_list.html"
    context_object_name = "mailings"


class ManagerMailingDetailView(LoginRequiredMixin, ManagerRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing/manager_mailing_detail.html"
    context_object_name = "mailing"


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        invalidate_home_cache(self.request.user.pk)
        return response


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_home_cache(self.request.user.pk)
        return response


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_delete_confirm.html"
    success_url = reverse_lazy("mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        invalidate_home_cache(self.request.user.pk)
        return response


@login_required
def send_mailing_view(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)

    try:
        attempts = send_mailing(mailing)

        invalidate_home_cache(request.user.pk)

        successful = sum(
            1 for attempt in attempts if attempt.status == MailingAttempt.STATUS_SUCCESS
        )

        failed = sum(
            1 for attempt in attempts if attempt.status == MailingAttempt.STATUS_FAILED
        )

        if failed:
            messages.warning(
                request,
                f"Рассылка завершена. " f"Успешно: {successful}, не успешно: {failed}.",
            )
        else:
            messages.success(
                request,
                f"Рассылка успешно отправлена." f"Получателей: {successful}.",
            )

    except ValueError as e:
        messages.error(request, str(e))

    return redirect("mailing_detail", pk=pk)


@login_required
def home(request):
    cache_key = f"home_stats_user_{request.user.pk}"

    cached_stats = cache.get(cache_key)

    if cached_stats is not None:
        return render(request, "mailing/home.html", cached_stats)

    now = timezone.now()

    user_mailings = Mailing.objects.filter(owner=request.user)

    for mailing in Mailing.objects.all():
        mailing.update_status()

    total_mailing = Mailing.objects.count()

    active_mailings = Mailing.objects.filter(
        start_time__lte=now, end_time__gte=now, status=Mailing.STATUS_STARTED
    ).count()

    total_recipients = Recipient.objects.filter(owner=request.user).count()

    successful_attempts = MailingAttempt.objects.filter(
        mailing__owner=request.user, status=MailingAttempt.STATUS_SUCCESS
    ).count()

    failed_attempts = MailingAttempt.objects.filter(
        mailing__owner=request.user, status=MailingAttempt.STATUS_FAILED
    ).count()

    send_message = successful_attempts

    context = {
        "total_mailing": total_mailing,
        "active_mailings": active_mailings,
        "total_recipients": total_recipients,
        "successful_attempts": successful_attempts,
        "failed_attempts": failed_attempts,
        "send_message": send_message,
    }

    cache.set(cache_key, context, timeout=60)

    return render(request, "mailing/home.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            profile = UserProfile.objects.create(user=user, email_verified=False)

            send_mail(
                subject="Подтверждение регистрации",
                message=(
                    "Для подтверждения регистрации перейдите по ссылке:\n\n"
                    f"http://127.0.0.1:8000/verify/{profile.verification_token}/"
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return redirect("verification_sent")

    else:
        form = RegistrationForm()

    return render(request, "mailing/register.html", {"form": form})


def verification_sent(request):
    return render(request, "mailing/verification_sent.html")


def verify_email(request, token):
    profile = get_object_or_404(UserProfile, verification_token=token)

    profile.email_verified = True
    profile.save(update_fields=["email_verified"])

    return redirect("login")


class ManagerUserListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = UserProfile
    template_name = "mailing/manager_user_list.html"
    context_object_name = "profiles"


@login_required
def manager_block_user(request, pk):
    if request.method != "POST":
        raise PermissionDenied

    if not hasattr(request.user, "profile"):
        raise PermissionDenied

    if request.user.profile.role != UserProfile.ROLE_MANAGER:
        raise PermissionDenied

    profile = get_object_or_404(UserProfile, pk=pk)

    if profile.user == request.user:
        messages.error(request, "Менеджер не может заблокировать самого себя.")
        return redirect("manager_user_list")

    profile.is_blocked = True
    profile.save(update_fields=["is_blocked"])

    messages.success(request, f"Пользователь {profile.user.username} заблокирован.")

    return redirect("manager_user_list")


@login_required
def manager_disable_mailing(request, pk):
    if request.method != "POST":
        raise PermissionDenied

    if not hasattr(request.user, "profile"):
        raise PermissionDenied

    if request.user.profile.role != UserProfile.ROLE_MANAGER:
        raise PermissionDenied

    mailing = get_object_or_404(Mailing, pk=pk)

    mailing.is_active = False
    mailing.save(update_fields=["is_active"])

    invalidate_home_cache(mailing.owner_id)

    messages.success(request, f"Рассылка #{mailing.pk} отключена.")

    return redirect("manager_mailing_list")
