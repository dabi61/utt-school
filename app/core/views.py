from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Schedule, Attendance
from .serializers import ScheduleSerializer, StudentScheduleSerializer

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