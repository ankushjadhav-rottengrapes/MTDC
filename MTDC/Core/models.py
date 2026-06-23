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
