from django.urls import path, include
from rest_framework import routers
from core.views import ClassViewSet, ScheduleViewSet
from core.admin import student_admin_site
from . import views

router = routers.DefaultRouter()
router.register(r'classes', ClassViewSet)
router.register(r'schedules', ScheduleViewSet, basename='schedule')

# URLs cho StudentAdminSite và API endpoints
urlpatterns = [
    # URLs student admin
    path('student-admin/', student_admin_site.urls),
    # API endpoints
    path('', include(router.urls)),
    path('', views.index_view, name='index'),
]
