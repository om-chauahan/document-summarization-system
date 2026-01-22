from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class StoredDocument(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="stored_documents",
	)

	original_name = models.CharField(max_length=255)
	content_type = models.CharField(max_length=127, blank=True)
	size_bytes = models.PositiveBigIntegerField(default=0)
	detected_type = models.CharField(max_length=32, blank=True)

	# Store the actual uploaded document in the DB (SQLite BLOB).
	file_bytes = models.BinaryField()

	extracted_text = models.TextField(blank=True)
	summary = models.TextField(blank=True)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.original_name} ({self.user_id})"


class UserCredits(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="credits",
	)
	credits = models.PositiveIntegerField(default=100)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name_plural = "User credits"

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.user_id}: {self.credits}"


class RazorpayTopupOrder(models.Model):
	STATUS_CREATED = "created"
	STATUS_PAID = "paid"
	STATUS_FAILED = "failed"

	STATUS_CHOICES = [
		(STATUS_CREATED, "Created"),
		(STATUS_PAID, "Paid"),
		(STATUS_FAILED, "Failed"),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="razorpay_topups",
	)
	plan_id = models.CharField(max_length=32)
	credits_to_add = models.PositiveIntegerField(default=0)
	amount_paise = models.PositiveIntegerField(default=0)
	currency = models.CharField(max_length=8, default="INR")

	razorpay_order_id = models.CharField(max_length=64, unique=True)
	razorpay_payment_id = models.CharField(max_length=64, blank=True)
	status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_CREATED)

	created_at = models.DateTimeField(auto_now_add=True)
	paid_at = models.DateTimeField(null=True, blank=True)

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.razorpay_order_id} ({self.status})"


@receiver(post_save, sender=get_user_model(), dispatch_uid="dss_create_user_credits")
def _create_user_credits(sender, instance, created, **kwargs):
	if not created:
		return
	# Create a credits row for every new account.
	UserCredits.objects.get_or_create(user=instance)
