from django.db import models


class master_mtdc(models.Model):
    property_id = models.IntegerField(primary_key=True)
    property_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True)
    region = models.CharField(max_length=100, blank=True)
    rp_zone = models.CharField(max_length=255, blank=True)
    dp_zone = models.CharField(max_length=255, blank=True)
    village = models.CharField(max_length=255, blank=True, default='')
    taluka = models.CharField(max_length=255, blank=True, default='')
    district = models.CharField(max_length=255, blank=True, default='')
    area_acres = models.CharField(max_length=100, blank=True, default='')
    area_hectare = models.CharField(max_length=100, blank=True, default='')
    survey_no = models.CharField(max_length=500, blank=True, default='')
    property_type = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
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


def property_image_upload_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4
    ext = Path(filename).suffix.lower()
    return f"properties/{instance.property_id}/images/{uuid4().hex}{ext}"


def property_document_upload_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4
    ext = Path(filename).suffix.lower()
    return f"properties/{instance.property_id}/documents/{uuid4().hex}{ext}"


class PropertyImage(models.Model):
    property_id = models.IntegerField()
    image = models.ImageField(upload_to=property_image_upload_path)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_propertyimage"
        ordering = ["-uploaded_at"]
        verbose_name = "Property Image"
        verbose_name_plural = "Property Images"

    def __str__(self):
        return f"Image for property {self.property_id} - {self.caption or 'No caption'}"


class PropertyDocument(models.Model):
    property_id = models.IntegerField()
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=property_document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_propertydocument"
        ordering = ["-uploaded_at"]
        verbose_name = "Property Document"
        verbose_name_plural = "Property Documents"

    def __str__(self):
        return f"Document for property {self.property_id} - {self.title}"



class PropertyVideo(models.Model):
    property = models.ForeignKey(
        master_mtdc,
        on_delete=models.CASCADE,
        related_name="videos",
        db_column="property_id",
        db_constraint=False,
    )
    youtube_url = models.URLField(max_length=500)
    title = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_propertyvideo"
        ordering = ["-uploaded_at"]
        verbose_name = "Property Video"
        verbose_name_plural = "Property Videos"

    def __str__(self):
        return f"Video for property {self.property_id} - {self.title or self.youtube_url}"


def validate_pdf(value):
    from pathlib import Path
    from django.core.exceptions import ValidationError
    if Path(value.name).suffix.lower() != '.pdf':
        raise ValidationError('Only PDF files are allowed for property maps.')


def property_map_upload_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4
    ext = Path(filename).suffix.lower()
    return f"properties/{instance.property_id}/maps/{uuid4().hex}{ext}"


class PropertyMap(models.Model):
    MAP_TYPE_CHOICES = [
        ('demarcation', 'Government Demarcation Map'),
        ('survey', 'Survey Map'),
    ]
    property_id = models.IntegerField()
    map_type = models.CharField(max_length=20, choices=MAP_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=property_map_upload_path, validators=[validate_pdf])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_propertymap"
        ordering = ["map_type", "-uploaded_at"]
        verbose_name = "Property Map"
        verbose_name_plural = "Property Maps"

    def __str__(self):
        return f"{self.get_map_type_display()} for property {self.property_id} - {self.title}"


class OccupancyJson(models.Model):
    year = models.CharField(max_length=20, unique=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_occupancyjson"
        ordering = ["year"]
        verbose_name = "Occupancy JSON"
        verbose_name_plural = "Occupancy JSONs"

    def __str__(self):
        return self.year

