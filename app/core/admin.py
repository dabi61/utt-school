from django.contrib import admin
from .models import Student, Teacher, Schedule, Attendance, QRCode, User, Classroom, Class, Object, Weekday
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import user_passes_test
from django.urls import path
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.shortcuts import redirect
from django.contrib import messages

def set_as_giangvien(modeladmin, request, queryset):
    group_gv, _ = Group.objects.get_or_create(name='GiangVien')
    group_sv = Group.objects.filter(name='SinhVien').first()

    for user in queryset:
        # Xoá khỏi nhóm Sinh viên nếu có
        if group_sv and group_sv in user.groups.all():
            user.groups.remove(group_sv)

        # Thêm vào nhóm Giảng viên nếu chưa có
        if group_gv not in user.groups.all():
            user.groups.add(group_gv)

        user.is_staff = True  # Cho phép truy cập admin nếu cần
        user.save()

        # Xoá bản ghi Student nếu tồn tại
        Student.objects.filter(user=user).delete()

        # Tạo bản ghi Teacher nếu chưa có
        teacher, created = Teacher.objects.get_or_create(user=user)
        if created:
            teacher.teacher_code = "GV" + str(user.id).zfill(4)
            teacher.save()

    messages.success(request, f"{queryset.count()} user(s) đã được chuyển sang Giảng viên.")

set_as_giangvien.short_description = "Chuyển thành Giảng viên"

def set_as_sinhvien(modeladmin, request, queryset):
    group_sv, _ = Group.objects.get_or_create(name='SinhVien')
    group_gv = Group.objects.filter(name='GiangVien').first()

    for user in queryset:
        # Xoá khỏi nhóm Giảng viên nếu có
        if group_gv and group_gv in user.groups.all():
            user.groups.remove(group_gv)

        # Thêm vào nhóm Sinh viên nếu chưa có
        if group_sv not in user.groups.all():
            user.groups.add(group_sv)

        user.is_staff = True  # Tuỳ chọn nếu sinh viên không cần vào admin
        user.save()

        # Xoá bản ghi Teacher nếu có
        Teacher.objects.filter(user=user).delete()

        # Tạo bản ghi Student nếu chưa có
        student, created = Student.objects.get_or_create(user=user)
        if created:
            student.student_code = "SV" + str(user.id).zfill(4)
            student.save()

    messages.success(request, f"{queryset.count()} user(s) đã được chuyển sang Sinh viên.")

set_as_sinhvien.short_description = "Chuyển thành Sinh viên"


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'password', 'name', 'is_active', 'groups')

# Tùy chỉnh UserAdmin
class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    actions = [set_as_giangvien, set_as_sinhvien]
    ordering = ['id']  # Sắp xếp theo ID
    form = UserAdminForm  # Sử dụng form tùy chỉnh
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('Permissions'),
            {
                'fields': ('groups',)
            }),
        (
            _('Important dates'),
            {'fields': ('last_login',)}
        ),
    )  # Cấu trúc trường trong phần chỉnh sửa người dùng
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'is_active',)
        }),
    )

    @admin.display(description="Vai trò")
    def role(self, obj):
        if obj.groups.filter(name="GiangVien").exists():
            return "Giảng viên"
        elif obj.groups.filter(name="SinhVien").exists():
            return "Sinh viên"
        return "Không xác định"
    # list_display nên như sau:
    list_display = ['email', 'role', ]

# Register models in the admin interface
admin.site.register(Student)
admin.site.register(User, UserAdmin)
admin.site.register(Teacher)
admin.site.register(Object)
admin.site.register(Classroom)
admin.site.register(Class)
admin.site.register(Weekday)
admin.site.register(Schedule)
admin.site.register(Attendance)
admin.site.register(QRCode)


# Tạo group nếu chưa tồn tại
for group_name in ['GiangVien', 'SinhVien']:
    Group.objects.get_or_create(name=group_name)