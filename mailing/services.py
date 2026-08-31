from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from .models import MailingAttempt


def invalidate_home_cache(user_id):
    cache.delete(f"home_stats_user_{user_id}")


def send_mailing(mailing):
    now = timezone.now()

    if not mailing.is_active:
        raise ValueError("Рассылка отключена менеджером.")

    if not (mailing.start_time <= now <= mailing.end_time):
        raise ValueError(
            "Рассылку можно отправить только в период между датой начала и датой окончания."
        )

    attempts = []

    for recipient in mailing.recipients.all():
        try:
            result = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=None,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            if result:
                attempts.append(
                    MailingAttempt(
                        mailing=mailing,
                        status=MailingAttempt.STATUS_SUCCESS,
                        server_response="Письмо успешно отправлено.",
                    )
                )
            else:
                attempts.append(
                    MailingAttempt(
                        mailing=mailing,
                        status=MailingAttempt.STATUS_FAILED,
                        server_response="Почтовый сервер не подтвердил отправку.",
                    )
                )

        except Exception as e:
            attempts.append(
                MailingAttempt(
                    mailing=mailing,
                    status=MailingAttempt.STATUS_FAILED,
                    server_response=str(e),
                )
            )

    MailingAttempt.objects.bulk_create(attempts)

    return attempts
