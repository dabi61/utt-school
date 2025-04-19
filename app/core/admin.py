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
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone

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

class ClassroomAdminForm(forms.ModelForm):
    manual_latitude = forms.FloatField(required=False, label="Nhập vĩ độ (latitude)")
    manual_longitude = forms.FloatField(required=False, label="Nhập kinh độ (longitude)")
    
    class Meta:
        model = Classroom
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['manual_latitude'].initial = instance.latitude
            self.fields['manual_longitude'].initial = instance.longitude
        self.fields['latitude'].widget = forms.HiddenInput()
        self.fields['longitude'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('manual_latitude') is not None:
            cleaned_data['latitude'] = cleaned_data.get('manual_latitude')
        if cleaned_data.get('manual_longitude') is not None:
            cleaned_data['longitude'] = cleaned_data.get('manual_longitude')
        return cleaned_data

class ClassroomAdmin(admin.ModelAdmin):
    form = ClassroomAdminForm
    list_display = ['classroom_code', 'class_name', 'location_info']
    search_fields = ['classroom_code', 'class_name']
    fields = ['classroom_code', 'class_name', 'manual_latitude', 'manual_longitude', 'latitude', 'longitude', 'map_view']
    readonly_fields = ['map_view']

    def location_info(self, obj):
        if obj.latitude and obj.longitude:
            return f"{obj.latitude:.6f}, {obj.longitude:.6f}"
        default_lat = 20.984505113573572
        default_lng = 105.79876021583512
        return f"{default_lat:.6f}, {default_lng:.6f} (mặc định)"
    location_info.short_description = "Vị trí"

    def map_view(self, obj):
        default_lat = 20.984505113573572
        default_lng = 105.79876021583512
        
        if obj and obj.latitude and obj.longitude:
            lat = obj.latitude
            lng = obj.longitude
            map_url = f"https://maps.google.com/maps?q={lat},{lng}&z=15&output=embed"
            location_text = f"{lat}, {lng}"
        else:
            lat = default_lat
            lng = default_lng
            map_url = f"https://maps.google.com/maps?q={lat},{lng}&z=15&output=embed"
            location_text = f"{lat}, {lng} (mặc định)"
        
        return format_html('''
            <div style="margin-bottom: 20px;">
                <h3>Vị trí hiện tại: {location}</h3>
                <p>Để thay đổi vị trí, hãy nhập tọa độ mới vào hai trường Latitude và Longitude phía trên.</p>
                <p>Có thể sử dụng <a href="https://www.google.com/maps/" target="_blank">Google Maps</a> để tìm tọa độ: click chuột phải vào điểm trên bản đồ và chọn "What's here?"</p>
                <iframe width="100%" height="400" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="{map_url}"></iframe>
            </div>
        ''', location=location_text, map_url=map_url)
    map_view.short_description = 'Bản đồ'
    
    class Media:
        js = ('https://maps.googleapis.com/maps/api/js?key=AIzaSyBEjmPyIZGCuEZL6mTq-e14U2xlCG-N2Z4',)

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'schedule', 'timestamp', 'is_present', 'is_late', 'minutes_late']
    list_filter = ['is_present', 'is_late', 'schedule__course_name', 'schedule__class_name']
    search_fields = ['student__user__name', 'schedule__course_name__object_name']
    readonly_fields = ['attendance_map', 'timestamp', 'latitude', 'longitude', 'location_source']
    
    def location_source(self, obj):
        if not obj.device_info:
            return "Không xác định"
        if "IP:" in obj.device_info:
            return "Vị trí dựa trên IP"
        return "GPS thiết bị"
    location_source.short_description = "Nguồn vị trí"
    
    def attendance_map(self, obj):
        # Lấy tọa độ phòng học
        classroom = obj.schedule.room
        classroom_lat = getattr(classroom, 'latitude', None)
        classroom_lng = getattr(classroom, 'longitude', None)
        
        # Tọa độ điểm danh của sinh viên
        student_lat = obj.latitude
        student_lng = obj.longitude
        
        # Tạo ID động cho bản đồ
        map_id = f"attendance_map_{obj.id}"
        
        # Nếu phòng học không có tọa độ
        if not classroom_lat or not classroom_lng:
            return "Phòng học chưa được cài đặt vị trí"
        
        # Nếu sinh viên không có dữ liệu tọa độ
        student_location_html = ""
        if student_lat and student_lng:
            student_location_html = f"""
            <h4>Vị trí điểm danh: {student_lat:.6f}, {student_lng:.6f}</h4>
            <p>Tình trạng: {"Có mặt" if obj.is_present else "Vắng mặt"} {f"(Trễ {obj.minutes_late} phút)" if obj.is_late else ""}</p>
            """
        
        return format_html(
            """
            <div>
                <h3>Vị trí phòng học {}: {:.6f}, {:.6f}</h3>
                {}
                <div id="{}" style="width: 100%; height: 400px;"></div>
                <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBEjmPyIZGCuEZL6mTq-e14U2xlCG-N2Z4&callback=initMap_{}"></script>
                <script>
                // Định nghĩa hàm khởi tạo với tên duy nhất cho mỗi bản đồ
                function initMap_{}() {{
                    if (document.getElementById('{}')) {{
                        // Tọa độ phòng học
                        var classroomLocation = {{ lat: {}, lng: {} }};
                        
                        // Tạo bản đồ
                        var map = new google.maps.Map(document.getElementById('{}'), {{
                            zoom: 15,
                            center: classroomLocation
                        }});
                        
                        // Đánh dấu vị trí phòng học
                        var classroomMarker = new google.maps.Marker({{
                            position: classroomLocation,
                            map: map,
                            title: 'Phòng học: {}',
                            icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
                        }});
                        
                        // Nếu có tọa độ sinh viên, thêm marker cho sinh viên
                        {}
                        
                        // Tự động điều chỉnh zoom để hiển thị cả hai marker nếu có
                        {}
                    }}
                }}
                </script>
            </div>
            """,
            classroom.class_name,
            classroom_lat,
            classroom_lng,
            student_location_html,
            map_id,
            obj.id,  # Thêm tham số duy nhất cho callback
            obj.id,  # Sử dụng tên hàm duy nhất
            map_id,
            classroom_lat,
            classroom_lng,
            map_id,
            classroom.class_name,
            """
            if ({student_lat} && {student_lng}) {{
                var studentLocation = {{ lat: parseFloat({0}), lng: parseFloat({1}) }};
                var studentMarker = new google.maps.Marker({{
                    position: studentLocation,
                    map: map,
                    title: 'Vị trí điểm danh của {2}',
                    icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
                }});
            }}
            """.format(student_lat, student_lng, obj.student.user.name) if student_lat and student_lng else "",
            """
            if ({student_lat} && {student_lng}) {{
                var bounds = new google.maps.LatLngBounds();
                bounds.extend(classroomLocation);
                bounds.extend(studentLocation);
                map.fitBounds(bounds);
            }}
            """.format(student_lat=student_lat, student_lng=student_lng) if student_lat and student_lng else ""
        )
    attendance_map.short_description = 'Bản đồ vị trí'
    
    def get_fieldsets(self, request, obj=None):
        if obj:  # Chỉ hiển thị bản đồ khi xem chi tiết
            return [
                (None, {'fields': ['student', 'schedule', 'is_present', 'is_late', 'minutes_late', 'timestamp']}),
                ('Thông tin vị trí', {'fields': ['latitude', 'longitude', 'location_source', 'device_info']}),
                ('Bản đồ', {'fields': ['attendance_map']}),
            ]
        return [
            (None, {'fields': ['student', 'schedule', 'is_present', 'is_late', 'minutes_late']}),
            ('Thông tin vị trí', {'fields': ['latitude', 'longitude', 'device_info']}),
        ]

class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'teacher', 'class_name', 'room', 'get_lesson_range', 'start_date', 'is_active']
    list_filter = ['is_active', 'course_name', 'teacher', 'class_name', 'room', 'lesson_start']
    search_fields = ['course_name__object_name', 'teacher__user__name', 'class_name__class_name']
    filter_horizontal = ['weekdays']
    exclude = ['qr_code', 'qr_code_data', 'start_time', 'end_time']  # Ẩn các trường QR code và thời gian tự động tính
    readonly_fields = ['qr_code_view', 'start_time_display', 'end_time_display']
    
    def start_time_display(self, obj):
        if obj.start_time:
            return timezone.localtime(obj.start_time).strftime('%H:%M:%S %d/%m/%Y')
        return "Chưa tính toán"
    start_time_display.short_description = "Thời gian bắt đầu"
    
    def end_time_display(self, obj):
        if obj.end_time:
            return timezone.localtime(obj.end_time).strftime('%H:%M:%S %d/%m/%Y')
        return "Chưa tính toán"
    end_time_display.short_description = "Thời gian kết thúc"
    
    def get_lesson_range(self, obj):
        end_lesson = obj.lesson_start + obj.lesson_count - 1
        if end_lesson > 11:
            end_lesson = 11
        return f"Tiết {obj.lesson_start} - {end_lesson}"
    get_lesson_range.short_description = "Tiết học"
    
    def get_fieldsets(self, request, obj=None):
        if obj:  # Chỉ hiển thị QR code khi xem chi tiết
            return [
                (None, {'fields': ['teacher', 'course_name', 'room', 'class_name']}),
                ('Tiết học', {'fields': ['lesson_start', 'lesson_count', 'start_time_display', 'end_time_display']}),
                ('Lịch trình', {'fields': ['start_date', 'end_date', 'weekdays', 'is_active']}),
                ('Mã QR', {'fields': ['qr_code_view']}),
            ]
        return [
            (None, {'fields': ['teacher', 'course_name', 'room', 'class_name']}),
            ('Tiết học', {'fields': ['lesson_start', 'lesson_count']}),
            ('Lịch trình', {'fields': ['start_date', 'end_date', 'weekdays', 'is_active']}),
        ]
    
    def qr_code_view(self, obj):
        if not obj.qr_code:
            return format_html(
                '''
                <p>Chưa có mã QR. Nhấn vào nút bên dưới để tạo mã QR.</p>
                <button onclick="window.location.href='/admin/core/schedule/{}/generate_qr/'" class="button">Tạo mã QR</button>
                ''',
                obj.id
            )
        
        return format_html(
            '''
            <div style="margin-bottom: 20px;">
                <h3>Mã QR cho lịch học</h3>
                <img src="{}" style="max-width: 300px; border: 1px solid #ddd; padding: 5px;">
                <p>Dữ liệu QR: <code>{}</code></p>
                <button onclick="window.location.href='/admin/core/schedule/{}/generate_qr/'" class="button">Tạo lại mã QR</button>
                <p><strong>Thời gian học:</strong> {} đến {}</p>
            </div>
            ''',
            obj.qr_code.url if obj.qr_code else '',
            obj.qr_code_data,
            obj.id,
            timezone.localtime(obj.start_time).strftime('%H:%M:%S %d/%m/%Y') if obj.start_time else 'Không xác định',
            timezone.localtime(obj.end_time).strftime('%H:%M:%S %d/%m/%Y') if obj.end_time else 'Không xác định'
        )
    qr_code_view.short_description = 'Mã QR'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generate_qr/', 
                 self.admin_site.admin_view(self.generate_qr_view), 
                 name='schedule-generate-qr'),
        ]
        return custom_urls + urls
    
    def generate_qr_view(self, request, object_id):
        schedule = self.get_object(request, object_id)
        schedule.generate_qr_code()
        messages.success(request, f"Đã tạo mã QR cho lịch học thành công.")
        return redirect(f'../../{object_id}/change/')
    
    def save_model(self, request, obj, form, change):
        # Kiểm tra số tiết hợp lệ
        if obj.lesson_count < 1:
            obj.lesson_count = 1
            messages.warning(request, "Số tiết phải lớn hơn hoặc bằng 1. Đã điều chỉnh thành 1.")
        
        if obj.lesson_start + obj.lesson_count - 1 > 11:
            obj.lesson_count = 11 - obj.lesson_start + 1
            messages.warning(request, f"Tiết kết thúc vượt quá giới hạn. Đã điều chỉnh số tiết thành {obj.lesson_count}.")
        
        super().save_model(request, obj, form, change)
        # Tự động tạo QR code khi tạo mới
        if not change and not obj.qr_code:
            obj.generate_qr_code()

# Register models in the admin interface
admin.site.register(Student)
admin.site.register(User, UserAdmin)
admin.site.register(Teacher)
admin.site.register(Object)
admin.site.register(Classroom, ClassroomAdmin)  # Sử dụng ClassroomAdmin
admin.site.register(Class)
admin.site.register(Weekday)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(QRCode)


# Tạo group nếu chưa tồn tại
for group_name in ['GiangVien', 'SinhVien']:
    Group.objects.get_or_create(name=group_name)