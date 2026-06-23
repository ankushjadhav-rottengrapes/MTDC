from django.contrib import admin

from .models import master_mtdc


@admin.register(master_mtdc)
class master_mtdc_admin(admin.ModelAdmin):
    list_display = ("property_id", "property_name", "category")
    search_fields = ("property_name", "category")
