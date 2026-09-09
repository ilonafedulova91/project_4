from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Mailing, MailingAttempt, Message, Recipient, UserProfile
from .services import invalidate_home_cache, send_mailing


class MailingTestDataMixin:
    def create_user(
        self,
        username="test_user",
        email="test_email@example.com",
        password="test_password",
        role=UserProfile.ROLE_USER,
        email_verified=True,
        is_active=True,
    ):

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=is_active,
        )

        UserProfile.objects.create(
            user=user,
            role=role,
            email_verified=email_verified,
        )

        return user


class MailingModelTests(MailingTestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()

        self.message = Message.objects.create(
            owner=self.user,
            subject="test_subject",
            body="test_body",
        )

        self.recipient = Recipient.objects.create(
            owner=self.user,
            email="recipient_email@example.com",
            full_name="test_recipient",
            comment="test_comment",
        )

    def test_mailing_time_validation_start_in_past(self):
        mailing = Mailing(
            owner=self.user,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
            message=self.message,
        )

        with self.assertRaises(Exception):
            mailing.full_clean()

    def test_mailing_time_validation_start_after_end(self):
        mailing = Mailing(
            owner=self.user,
            start_time=timezone.now() + timedelta(hours=2),
            end_time=timezone.now() + timedelta(hours=1),
            message=self.message,
        )

        with self.assertRaises(Exception):
            mailing.full_clean()

    def test_mailing_time_validation_normal_period(self):
        mailing = Mailing(
            owner=self.user,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            message=self.message,
        )

        mailing.full_clean()


class MailingServiceTests(MailingTestDataMixin, TestCase):
    def setUp(self):
        self.user = self.create_user()

        self.message = Message.objects.create(
            owner=self.user,
            subject="test_subject",
            body="test_body",
        )

        self.recipient_1 = Recipient.objects.create(
            owner=self.user,
            email="recipient_1_email@example.com",
            full_name="test_recipient_1",
        )

        self.recipient_2 = Recipient.objects.create(
            owner=self.user,
            email="recipient_2_email@example.com",
            full_name="test_recipient_2",
        )

        self.mailing = Mailing.objects.create(
            owner=self.user,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            message=self.message,
        )

        self.mailing.recipients.set(
            [self.recipient_1, self.recipient_2],
        )

    @patch("mailing.services.send_mail")
    def test_successful_attempts_saved_bulk_create(
        self,
        mock_send_mail,
    ):
        mock_send_mail.return_value = 1

        with patch.object(
            MailingAttempt.objects,
            "bulk_create",
            wraps=MailingAttempt.objects.bulk_create,
        ) as mock_bulk_create:

            attempts = send_mailing(self.mailing)

        self.assertEqual(len(attempts), 2)
        self.assertEqual(MailingAttempt.objects.filter(mailing=self.mailing).count(), 2)
        self.assertTrue(mock_bulk_create.called)
        self.assertEqual(mock_bulk_create.call_count, 1)

        created_attempts = mock_bulk_create.call_args.args[0]

        self.assertEqual(len(created_attempts), 2)

        for attempt in created_attempts:
            self.assertEqual(
                attempt.status,
                MailingAttempt.STATUS_SUCCESS,
            )

        self.assertEqual(mock_send_mail.call_count, 2)

    @patch("mailing.services.send_mail")
    def test_failed_attempts_saved(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP error")

        attempts = send_mailing(self.mailing)

        self.assertEqual(len(attempts), 2)
        self.assertEqual(
            MailingAttempt.objects.filter(
                mailing=self.mailing,
                status=MailingAttempt.STATUS_FAILED,
            ).count(),
            2,
        )

        for attempt in attempts:
            self.assertEqual(
                attempt.status,
                MailingAttempt.STATUS_FAILED,
            )
            self.assertEqual(
                attempt.server_response,
                "SMTP error",
            )

    def test_mailing_outside_allowed_period(self):
        self.mailing.start_time = timezone.now() + timedelta(hours=1)
        self.mailing.end_time = timezone.now() + timedelta(hours=2)
        self.mailing.save(
            update_fields=["start_time", "end_time"],
        )

        with self.assertRaises(ValueError):
            send_mailing(self.mailing)

    def test_disabled_mailing(self):
        self.mailing.is_active = False
        self.mailing.save(update_fields=["is_active"])

        with self.assertRaises(ValueError):
            send_mailing(self.mailing)


class AccessControlTests(MailingTestDataMixin, TestCase):
    def setUp(self):
        self.user_1 = self.create_user(
            username="test_user_1",
            email="test_user_1@example.com",
        )

        self.user_2 = self.create_user(
            username="test_user_2",
            email="test_user_2@example.com",
        )

        self.recipient_1 = Recipient.objects.create(
            owner=self.user_1,
            email="test_recipient_1@example.com",
            full_name="test_recipient_1",
        )

        self.recipient_2 = Recipient.objects.create(
            owner=self.user_2,
            email="test_recipient_2@example.com",
            full_name="test_recipient_2",
        )

    def test_user_sees_only_own_recipients(self):
        self.client.force_login(self.user_1)

        response = self.client.get(reverse("recipient_list"))

        self.assertContains(
            response,
            self.recipient_1.full_name,
        )

        self.assertNotContains(
            response,
            self.recipient_2.full_name,
        )

    def test_user_cannot_open_other_user_recipients(self):
        self.client.force_login(self.user_1)

        response = self.client.get(
            reverse(
                "recipient_detail",
                kwargs={"pk": self.recipient_2.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_edit_other_recipients(self):
        self.client.force_login(self.user_1)

        response = self.client.get(
            reverse(
                "recipient_update",
                kwargs={"pk": self.recipient_2.pk},
            )
        )

        self.assertEqual(response.status_code, 404)


class AuthenticationTests(MailingTestDataMixin, TestCase):
    def test_unverified_user_cannot_login(self):
        user = self.create_user(
            username="unverified_user",
            email="unverified_user@example.com",
            email_verified=False,
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": user.username,
                "password": "test_password",
            },
        )

        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_inactive_user_cannot_login(self):
        user = self.create_user(
            username="inactive_user",
            email="inactive_user@example.com",
            email_verified=True,
            is_active=False,
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": user.username,
                "password": "test_password",
            },
        )

        self.assertFalse(response.wsgi_request.user.is_authenticated)


class ManagerActionsTests(MailingTestDataMixin, TestCase):
    def setUp(self):
        self.manager = self.create_user(
            username="manager",
            email="test_manager@example.com",
            role=UserProfile.ROLE_MANAGER,
        )

        self.user = self.create_user(
            username="test_user",
            email="test_user@example.com",
        )

    def test_manager_can_block_user(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse(
                "manager_block_user",
                kwargs={"pk": self.user.profile.pk},
            )
        )

        self.assertRedirects(response, reverse("manager_user_list"))
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.profile.is_blocked)

    def test_normal_user_cannot_block_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("manager_block_user", kwargs={"pk": self.manager.profile.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_manager_can_disable_mailing(self):
        message = Message.objects.create(
            owner=self.user,
            subject="test_subject",
            body="test_body",
        )

        mailing = Mailing.objects.create(
            owner=self.user,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            message=message,
        )

        self.client.force_login(self.manager)

        response = self.client.post(
            reverse(
                "manager_disable_mailing",
                kwargs={"pk": mailing.pk},
            )
        )

        self.assertRedirects(response, reverse("manager_mailing_list"))

        mailing.refresh_from_db()

        self.assertFalse(mailing.is_active)


class CacheTests(MailingTestDataMixin, TestCase):
    def setUp(self):
        cache.clear()

        self.user = self.create_user(
            username="cache_user",
            email="cache_user@example.com",
        )

    def tearDown(self):
        cache.clear()

    def test_cache_stores_retrieve_statistics(self):
        cache_key = f"home_stats_user_{self.user.pk}"

        statistics = {
            "total_mailings": 5,
            "active_mailings": 2,
            "total_recipients": 10,
            "successful_attempts": 7,
            "failed_attempts": 1,
            "sent_messages": 7,
        }

        cache.set(
            cache_key,
            statistics,
            timeout=60,
        )

        self.assertEqual(
            cache.get(cache_key),
            statistics,
        )

    def test_user_cache_invalidated(self):
        cache_key = f"home_stats_user_{self.user.pk}"

        cache.set(
            cache_key,
            {"total_mailings": 5},
            timeout=60,
        )

        self.assertIsNotNone(cache.get(cache_key))

        invalidate_home_cache(self.user.pk)

        self.assertIsNone(cache.get(cache_key))
