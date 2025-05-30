# Generated by Django 5.2 on 2025-04-18 12:27

import core.models
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_remove_class_course_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="end_date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="schedule",
            name="is_active",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="schedule",
            name="start_date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="schedule",
            name="weekdays",
            field=models.CharField(
                choices=[
                    ("MON", "Thứ 2"),
                    ("TUE", "Thứ 3"),
                    ("WED", "Thứ 4"),
                    ("THU", "Thứ 5"),
                    ("FRI", "Thứ 6"),
                    ("SAT", "Thứ 7"),
                ],
                default="MON",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="qr_code",
            field=models.ImageField(
                blank=True, null=True, upload_to=core.models.generate_qr_code_path
            ),
        ),
    ]
