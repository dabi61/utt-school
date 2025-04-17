from rest_framework import serializers
from ..models import Schedule

class ScheduleQRSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.name', read_only=True)
    course_name = serializers.CharField(source='course_name.object_name', read_only=True)
    room_name = serializers.CharField(source='room.classroom_code', read_only=True)
    class_name = serializers.CharField(source='class_name.class_name', read_only=True)
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            'id', 'teacher_name', 'course_name', 'room_name', 
            'class_name', 'start_time', 'end_time', 'qr_code_url'
        ]

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None 