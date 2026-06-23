from django.db import models


class master_mtdc(models.Model):
    property_id = models.IntegerField(primary_key=True)
    property_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True)
    pt_geom = models.TextField(null=True, blank=True)
    pl_geom = models.TextField(null=True, blank=True)
    poly_geom = models.TextField(null=True, blank=True)
    centroid = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "master_mtdc"
        verbose_name = "master_mtdc"
        verbose_name_plural = "master_mtdc"

    def __str__(self):
        return f"{self.property_id} - {self.property_name}"


def property_cover_upload_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4
    ext = Path(filename).suffix.lower()
    return f"properties/{instance.property_id}/cover/{uuid4().hex}{ext}"


class PropertyCover(models.Model):
    property_id = models.IntegerField(unique=True)
    cover_image = models.ImageField(upload_to=property_cover_upload_path)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_propertycover"
        verbose_name = "Property Cover Photo"
        verbose_name_plural = "Property Cover Photos"

    def __str__(self):
        return f"Cover for property {self.property_id}"
