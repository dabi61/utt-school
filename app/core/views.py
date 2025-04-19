from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Schedule, Attendance, Class
from .serializers import ScheduleSerializer, StudentScheduleSerializer
from django.shortcuts import render

class ClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint cho xem thông tin lớp học
    Chỉ cung cấp chức năng đọc (không thêm/sửa/xóa)
    """
    queryset = Class.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        # Sử dụng serializer mặc định của DRF
        from rest_framework import serializers
        
        class ClassSerializer(serializers.ModelSerializer):
            students_count = serializers.SerializerMethodField()
            teachers_count = serializers.SerializerMethodField()
            
            class Meta:
                model = Class
                fields = ['id', 'class_code', 'class_name', 'students_count', 'teachers_count']
            
            def get_students_count(self, obj):
                return obj.students.count()
                
            def get_teachers_count(self, obj):
                return obj.teachers.count()
        
        return ClassSerializer
    
    def get_queryset(self):
        """
        Lọc dữ liệu dựa trên vai trò người dùng:
        - Sinh viên: chỉ thấy các lớp mình tham gia
        - Giáo viên: chỉ thấy các lớp mình dạy
        - Admin: thấy tất cả
        """
        user = self.request.user
        
        if user.is_superuser:
            return Class.objects.all()
            
        # Kiểm tra nếu là sinh viên
        try:
            student = user.student
            return Class.objects.filter(students=student)
        except:
            pass
            
        # Kiểm tra nếu là giáo viên
        try:
            teacher = user.teacher
            return Class.objects.filter(teachers=teacher)
        except:
            return Class.objects.none()

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'student_schedule':
            return StudentScheduleSerializer
        return ScheduleSerializer

    @action(detail=False, methods=['get'])
    def student_schedule(self, request):
        # Lấy tất cả lịch học của các lớp mà sinh viên đang học
        student = request.user.student
        schedules = Schedule.objects.filter(class_name__students=student)
        
        # Sắp xếp theo thời gian bắt đầu
        schedules = schedules.order_by('start_time')
        
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_attendance(self, request, pk=None):
        schedule = self.get_object()
        student = request.user.student
        
        # Kiểm tra xem sinh viên có trong lớp không
        if student not in schedule.class_name.students.all():
            return Response(
                {"error": "Bạn không phải là sinh viên của lớp này."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cập nhật hoặc tạo bản ghi điểm danh
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            schedule=schedule,
            defaults={'is_present': True}
        )
        
        if not created:
            attendance.is_present = True
            attendance.save()
        
        return Response({"status": "success", "message": "Điểm danh thành công."})

def index_view(request):
    """
    Hiển thị trang chủ với các tùy chọn đăng nhập
    """
    return render(request, 'index.html') 