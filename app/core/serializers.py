from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Schedule, Attendance
from django.utils import timezone

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'name')
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Mật khẩu không khớp."})
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email đã tồn tại.")
        return value

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            name=validated_data['name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class StudentScheduleSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.name', read_only=True)
    course_name = serializers.CharField(source='course_name.object_name', read_only=True)
    room_name = serializers.CharField(source='room.classroom_code', read_only=True)
    class_name = serializers.CharField(source='class_name.class_name', read_only=True)
    is_present = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            'id', 'teacher_name', 'course_name', 'room_name', 
            'class_name', 'start_time', 'end_time', 'is_present'
        ]

    def get_is_present(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            student = request.user.student
            attendance = Attendance.objects.filter(
                student=student,
                schedule=obj
            ).first()
            return attendance.is_present if attendance else None
        return None

class ScheduleSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.name', read_only=True)
    course_name = serializers.CharField(source='course_name.object_name', read_only=True)
    room_name = serializers.CharField(source='room.classroom_code', read_only=True)
    class_name = serializers.CharField(source='class_name.class_name', read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'teacher_name', 'course_name', 'room_name', 
            'class_name', 'start_time', 'end_time'
        ]

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError("Thời gian kết thúc phải sau thời gian bắt đầu.")
            
            if start_time < timezone.now():
                raise serializers.ValidationError("Không thể tạo lịch học trong quá khứ.")

            # Kiểm tra xung đột lịch học
            conflicting_schedules = Schedule.objects.filter(
                room=attrs.get('room'),
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(id=self.instance.id if self.instance else None)

            if conflicting_schedules.exists():
                raise serializers.ValidationError("Phòng học đã được sử dụng trong khoảng thời gian này.")

        return attrs

    def create(self, validated_data):
        schedule = super().create(validated_data)
        
        # Tạo bản ghi điểm danh cho tất cả sinh viên trong lớp
        students = schedule.class_name.students.all()
        for student in students:
            Attendance.objects.create(
                student=student,
                schedule=schedule,
                is_present=False
            )
            
        return schedule 