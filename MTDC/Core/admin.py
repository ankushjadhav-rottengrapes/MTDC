from django.contrib import admin

from .models import master_mtdc, PropertyCover, PropertyDocument, PropertyImage


@admin.register(master_mtdc)
class master_mtdc_admin(admin.ModelAdmin):
    list_display = ("property_id", "property_name", "category")
    search_fields = ("property_name", "category")


@admin.register(PropertyCover)
class PropertyCoverAdmin(admin.ModelAdmin):
    list_display = ("property_id", "cover_image", "updated_at")
    search_fields = ("property_id",)


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property_id", "caption", "uploaded_at")
    search_fields = ("property_id", "caption")
    list_filter = ("uploaded_at",)


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ("property_id", "title", "uploaded_at")
    search_fields = ("property_id", "title")
    list_filter = ("uploaded_at",)