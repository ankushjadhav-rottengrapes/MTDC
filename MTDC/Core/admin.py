from django import forms
from django.contrib import admin

from .models import master_mtdc, PropertyCover, PropertyDocument, PropertyImage, PropertyVideo


@admin.register(master_mtdc)
class master_mtdc_admin(admin.ModelAdmin):
    list_display = ("property_id", "property_name", "category")
    search_fields = ("property_name", "category")


class PropertyCoverForm(forms.ModelForm):
    property_id = forms.ModelChoiceField(
        queryset=master_mtdc.objects.all().order_by("property_name"),
        to_field_name="property_id",
        label="Property",
    )

    class Meta:
        model = PropertyCover
        fields = "__all__"

    def clean_property_id(self):
        return self.cleaned_data["property_id"].property_id


@admin.register(PropertyCover)
class PropertyCoverAdmin(admin.ModelAdmin):
    form = PropertyCoverForm
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


admin.site.register(PropertyVideo)