"""
Views for the user API.
"""

from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings  # Sửa lỗi chính tả ở đây


from user.serializers import UserSerializer, AuthTokenSerializer

# CreateApiView:
#   POST để tạo object mới
#   auto xử lý serialization
#   auto validate
#   auto trả về response phù hợp


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer

# ObtainAuthToken
#   Xử lý authentication
#   Tạo token cho user
#   Quản lý session
#   Các tính nagw kế thừa
#   post()
#   get_serializer_context: Context cho serializer
#   Token generation logic


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

# RetrieveUpdateAPIView
# GET: Lấy thông tin của object
# PUT/PATCH: cập nhật object
# Tự động xử lý serialization
# Các tính năng kế thừa
#   get(): xử lý get request
#   put(): xử lý Put request
#   patch(): xử lý patch request
#   get_object(): Lấy object cần xử lý


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    # TokenAuthentication
    # Xác thực bằng token
    # kiểm tra token header
    # xác định user từ token
    authentication_classes = [authentication.TokenAuthentication]
    # IsAuthenticated
    # Kiểm tra user đã đăng nhập
    # Chạn access từ anonymous users
    # Bảo vệ endpoint
    permission_classes = [permissions.IsAuthenticated]

    # Override get_object
    # Trả về user hiện tại
    # Không cần query database
    # Đơn giản hóa logic

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user
