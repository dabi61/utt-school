from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Student, Teacher, Class, Classroom, Object, Schedule, Attendance
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

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'email')
        extra_kwargs = {
            'email': {'read_only': True}
        }

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Tên không được để trống.")
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mật khẩu cũ không đúng.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Mật khẩu mới không khớp."})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class StudentSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()

    class Meta:
        model = Student
        fields = ('id', 'user', 'student_code')
        read_only_fields = ('student_code',)

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserCreateSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            student = Student.objects.create(user=user, **validated_data)
            return student
        raise serializers.ValidationError(user_serializer.errors)

class TeacherSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()

    class Meta:
        model = Teacher
        fields = ('id', 'user', 'teacher_code')
        read_only_fields = ('teacher_code',)

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserCreateSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            teacher = Teacher.objects.create(user=user, **validated_data)
            return teacher
        raise serializers.ValidationError(user_serializer.errors)

class UserDetailSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    student_code = serializers.SerializerMethodField()
    teacher_code = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'role', 'student_code', 'teacher_code')

    def get_role(self, obj):
        if hasattr(obj, 'student'):
            return 'student'
        elif hasattr(obj, 'teacher'):
            return 'teacher'
        return None

    def get_student_code(self, obj):
        if hasattr(obj, 'student'):
            return obj.student.student_code
        return None

    def get_teacher_code(self, obj):
        if hasattr(obj, 'teacher'):
            return obj.teacher.teacher_code
        return None

class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = ('id', 'object_code', 'object_name')
        read_only_fields = ('object_code',)

    def validate_object_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Tên môn học không được để trống.")
        if len(value) < 2:
            raise serializers.ValidationError("Tên môn học phải có ít nhất 2 ký tự.")
        return value

class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ('id', 'classroom_code', 'class_name')
        read_only_fields = ('classroom_code',)

    def validate_class_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Tên phòng học không được để trống.")
        if len(value) < 2:
            raise serializers.ValidationError("Tên phòng học phải có ít nhất 2 ký tự.")
        return value

class ClassSerializer(serializers.ModelSerializer):
    students = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Student.objects.all(),
        required=False
    )
    course_name = serializers.CharField(source='course_name.object_name', read_only=True)
    class_name = serializers.CharField(read_only=True)

    class Meta:
        model = Class
        fields = ('id', 'class_name', 'course_name', 'students')
        read_only_fields = ('class_name',)

    def validate(self, attrs):
        # Kiểm tra nếu có students trong attrs
        if 'students' in attrs:
            students = attrs['students']
            if len(students) > 50:  # Giới hạn số lượng sinh viên trong một lớp
                raise serializers.ValidationError("Một lớp không thể có quá 50 sinh viên.")
        return attrs

    def create(self, validated_data):
        students = validated_data.pop('students', [])
        class_instance = Class.objects.create(**validated_data)
        class_instance.students.set(students)
        return class_instance

    def update(self, instance, validated_data):
        students = validated_data.pop('students', None)
        if students is not None:
            instance.students.set(students)
        return super().update(instance, validated_data)

class ClassDetailSerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True, read_only=True)
    course_name = ObjectSerializer(read_only=True)

    class Meta:
        model = Class
        fields = ('id', 'class_name', 'course_name', 'students')

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
    students = StudentSerializer(many=True, read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'teacher_name', 'course_name', 'room_name', 
            'class_name', 'start_time', 'end_time', 'students'
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