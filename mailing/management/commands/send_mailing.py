from django.contrib.messages import success
from django.core.management.base import BaseCommand, CommandError

from mailing.models import Mailing, MailingAttempt
from mailing.services import send_mailing


class Command(BaseCommand):
    help = "Отправляет указанную рассылку."

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int, help="ID рассылки")

    def handle(self, *args, **options):
        mailing_id = options["mailing_id"]

        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            raise CommandError(f"Рассылка с ID {mailing_id} не найдена.")

        try:
            attempts = send_mailing(mailing)
        except ValueError as e:
            raise CommandError(str(e))

        successful = sum(
            attempt.status == MailingAttempt.STATUS_SUCCESS for attempt in attempts
        )

        failed = sum(
            attempt.status == MailingAttempt.STATUS_FAILED for attempt in attempts
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Рассылка #{mailing.pk} завершена. "
                f"Успешно: {successful}, не успешно: {failed}."
            )
        )
