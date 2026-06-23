from django.contrib import admin

from .models import (
    master_mtdc,
    Property,
    Property3DModel,
    PropertyDocument,
    PropertyImage,
    PropertyVideo,
)


class PropertyDocumentInline(admin.TabularInline):
    model = PropertyDocument
    extra = 1
    fields = ("title", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("caption", "image", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ("title", "video", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class Property3DModelInline(admin.TabularInline):
    model = Property3DModel
    extra = 1
    fields = ("title", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("property_id", "name", "cover_image", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "property_id")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("property_id", "name", "description", "cover_image", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    inlines = (
        PropertyDocumentInline,
        PropertyImageInline,
        PropertyVideoInline,
        Property3DModelInline,
    )


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "property", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("title", "property__name", "property__property_id")
    autocomplete_fields = ("property",)
    readonly_fields = ("uploaded_at",)


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("caption", "property", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("caption", "property__name", "property__property_id")
    autocomplete_fields = ("property",)
    readonly_fields = ("uploaded_at",)


@admin.register(PropertyVideo)
class PropertyVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "property", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("title", "property__name", "property__property_id")
    autocomplete_fields = ("property",)
    readonly_fields = ("uploaded_at",)


@admin.register(Property3DModel)
class Property3DModelAdmin(admin.ModelAdmin):
    list_display = ("title", "property", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("title", "property__name", "property__property_id")
    autocomplete_fields = ("property",)
    readonly_fields = ("uploaded_at",)


@admin.register(master_mtdc)
class master_mtdc_admin(admin.ModelAdmin):
    list_display = ("property_id", "property_name", "category")
    search_fields = ("property_id", "property_name", "category")
