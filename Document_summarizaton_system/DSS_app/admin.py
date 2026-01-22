from django.contrib import admin

from .models import StoredDocument, UserCredits


@admin.register(StoredDocument)
class StoredDocumentAdmin(admin.ModelAdmin):
	list_display = ("id", "original_name", "user", "detected_type", "size_bytes", "created_at")
	list_filter = ("detected_type", "created_at")
	search_fields = ("original_name", "user__username", "user__email")


@admin.register(UserCredits)
class UserCreditsAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "credits", "updated_at")
	search_fields = ("user__username", "user__email")
	list_filter = ("updated_at",)
