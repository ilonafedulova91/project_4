from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Mailing, Message, Recipient


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ("email", "full_name", "comment")


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("subject", "body")


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ("start_time", "end_time", "message", "recipients")
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["recipients"].queryset = Recipient.objects.filter(owner=user)

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and start_time < timezone.now():
            self.add_error("start_time", "Дата и время начала не могут быть в прошлом.")

        if start_time and end_time and start_time >= end_time:
            self.add_error("end_time", "Дата окончания должна быть позже даты начала.")

        return cleaned_data


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")

        return email
