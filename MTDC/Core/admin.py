from django.contrib import admin

from .models import master_mtdc, PropertyCover


@admin.register(master_mtdc)
class master_mtdc_admin(admin.ModelAdmin):
    list_display = ("property_id", "property_name", "category")
    search_fields = ("property_name", "category")


@admin.register(PropertyCover)
class PropertyCoverAdmin(admin.ModelAdmin):
    list_display = ("property_id", "cover_image", "updated_at")
    search_fields = ("property_id",)
