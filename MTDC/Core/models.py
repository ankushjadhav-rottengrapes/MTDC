from pathlib import Path
from uuid import uuid4

from django.core.validators import FileExtensionValidator
from django.db import models


def property_asset_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return (
        f"properties/{instance.property.property_id}/"
        f"{instance.asset_directory}/{uuid4().hex}{extension}"
    )


def property_cover_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"properties/{instance.property_id}/cover/{uuid4().hex}{extension}"


class Property(models.Model):
    property_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to=property_cover_upload_path, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["property_id"]
        verbose_name_plural = "properties"

    def __str__(self):
        return f"{self.property_id} - {self.name}"


class PropertyDocument(models.Model):
    asset_directory = "documents"

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=property_asset_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.property}: {self.title}"


class PropertyImage(models.Model):
    asset_directory = "images"

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to=property_asset_upload_path)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.caption or f"Image for {self.property}"


class PropertyVideo(models.Model):
    asset_directory = "videos"

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="videos",
    )
    title = models.CharField(max_length=255)
    video = models.FileField(upload_to=property_asset_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.property}: {self.title}"


class Property3DModel(models.Model):
    asset_directory = "3d-models"

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="models_3d",
    )
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to=property_asset_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["glb", "gltf", "obj", "dem"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "property 3D model"
        verbose_name_plural = "property 3D models"

    def __str__(self):
        return f"{self.property}: {self.title}"


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
