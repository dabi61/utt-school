# core/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from core.models import Student
import uuid

@receiver(post_save, sender=User)
def create_student_for_user(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        # tránh tạo trùng student nếu đã có
        if not hasattr(instance, 'student'):
            Student.objects.create(
                user=instance,
                student_code=str(uuid.uuid4())[:8]  # mã ngẫu nhiên
            )
