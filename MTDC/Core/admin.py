from django import forms
from django.contrib import admin

from .models import master_mtdc, PropertyCover, PropertyDocument, PropertyImage, PropertyVideo


class PropertyIdForm(forms.ModelForm):
    property_id = forms.ModelChoiceField(
        queryset=master_mtdc.objects.all().order_by("property_name"),
        to_field_name="property_id",
        label="Property",
    )

    def clean_property_id(self):
        return self.cleaned_data["property_id"].property_id


class PropertyCoverForm(PropertyIdForm):
    class Meta:
        model = PropertyCover
        fields = "__all__"


class PropertyImageForm(PropertyIdForm):
    class Meta:
        model = PropertyImage
        fields = "__all__"


class PropertyDocumentForm(PropertyIdForm):
    class Meta:
        model = PropertyDocument
        fields = "__all__"


class MasterMtdcAdmin(admin.ModelAdmin):
    list_display = ("property_id", "property_name", "category")
    search_fields = ("property_name", "category")


class PropertyCoverAdmin(admin.ModelAdmin):
    form = PropertyCoverForm
    list_display = ("property_id", "cover_image", "updated_at")


class PropertyImageAdmin(admin.ModelAdmin):
    form = PropertyImageForm
    list_display = ("property_id", "caption", "uploaded_at")
    list_filter = ("uploaded_at",)


class PropertyDocumentAdmin(admin.ModelAdmin):
    form = PropertyDocumentForm
    list_display = ("property_id", "title", "uploaded_at")
    list_filter = ("uploaded_at",)


class PropertyVideoAdmin(admin.ModelAdmin):
    list_display = ("property", "title", "youtube_url", "uploaded_at")
    search_fields = ("property__property_name", "title")
    list_filter = ("uploaded_at",)


admin.site.register(master_mtdc, MasterMtdcAdmin)
admin.site.register(PropertyCover, PropertyCoverAdmin)
admin.site.register(PropertyImage, PropertyImageAdmin)
admin.site.register(PropertyDocument, PropertyDocumentAdmin)
admin.site.register(PropertyVideo, PropertyVideoAdmin)
