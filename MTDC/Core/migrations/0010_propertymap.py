from django.db import migrations, models
import Core.models


class Migration(migrations.Migration):

    dependencies = [
        ('Core', '0009_occupancyjson'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropertyMap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('property_id', models.IntegerField()),
                ('map_type', models.CharField(choices=[('demarcation', 'Government Demarcation Map'), ('survey', 'Survey Map')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to=Core.models.property_map_upload_path)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Property Map',
                'verbose_name_plural': 'Property Maps',
                'db_table': 'core_propertymap',
                'ordering': ['map_type', '-uploaded_at'],
            },
        ),
    ]
