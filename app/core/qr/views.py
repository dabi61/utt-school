from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Schedule
from .serializers import ScheduleQRSerializer

class ScheduleQRViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleQRSerializer

    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        schedule = self.get_object()
        try:
            qr_code_url = schedule.generate_qr_code()
            return Response({
                'status': 'success',
                'message': 'QR code generated successfully',
                'qr_code_url': qr_code_url
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 