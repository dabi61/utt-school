"""
Database models.
"""
import uuid
import os
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    Group,
    Permission,
)

def generate_student_code():
    return f"SV{uuid.uuid4().hex[:6].upper()}"

def generate_teacher_code():
    return f"GV{uuid.uuid4().hex[:6].upper()}"

def generate_class_code():
    return f"C{uuid.uuid4().hex[:6].upper()}"

def generate_classroom_code():
    return f"CR{uuid.uuid4().hex[:6].upper()}"

def generate_object_code():
    return f"O{uuid.uuid4().hex[:6].upper()}"

class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """Create, save and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model."""
    app_label = 'core'
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

# models.py
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_code = models.CharField(max_length=100, unique=True, default=generate_student_code)

    def __str__(self):
        return self.user.email

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_code = models.CharField(max_length=100, unique=True, default=generate_teacher_code)

    def __str__(self):
        return self.user.email

class Class(models.Model):
    class_code = models.CharField(max_length=100, unique=True, default=generate_class_code)
    class_name = models.CharField(max_length=100)
    students = models.ManyToManyField(Student, related_name='classes')

    def __str__(self):
        return f"{self.class_code} - {self.class_name}"


class Classroom(models.Model):
    classroom_code = models.CharField(max_length=100, unique=True, default=generate_classroom_code)
    class_name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.class_name} ({self.classroom_code})"
    
class Object(models.Model):
    object_code = models.CharField(max_length=100, unique=True, default=generate_object_code)
    object_name = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.object_name} ({self.object_code})"

def generate_qr_code_path(instance, filename):
    # Tạo đường dẫn lưu trữ QR code theo cấu trúc: qr_codes/YYYY/MM/DD/schedule_id.png
    date = instance.start_time.date()
    return f'qr_codes/{date.year}/{date.month}/{date.day}/{instance.id}.png'

class Schedule(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course_name = models.ForeignKey(Object, on_delete=models.CASCADE)
    room = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    qr_code = models.ImageField(upload_to=generate_qr_code_path, blank=True, null=True)
    qr_code_data = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.course_name} by {self.teacher.user.name}"

    def generate_qr_code(self):
        if not self.qr_code_data:
            # Tạo dữ liệu cho QR code
            data = {
                'schedule_id': self.id,
                'course_name': self.course_name.object_name,
                'teacher': self.teacher.user.name,
                'class_name': self.class_name.class_name,
                'room': self.room.classroom_code,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            }
            self.qr_code_data = str(data)
            self.save()

        # Tạo QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_code_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Lưu QR code vào file
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        # Lưu file vào trường qr_code
        self.qr_code.save(f'{self.id}.png', File(buffer), save=True)
        return self.qr_code.url

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_present = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.user.name} - {self.schedule.course_name}"


class QRCode(models.Model):
    schedule = models.OneToOneField(Schedule, on_delete=models.CASCADE)
    qr_code_data = models.TextField()

    def __str__(self):
        return f"QR Code for {self.schedule.course_name}"