from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, ProductViewSet, ImageViewSet, CollectionViewSet, CommentViewSet,
    OrderViewSet, OrderItemViewSet, SpinnerRewardViewSet, UserSpinnerHistoryViewSet,
    PointHistoryViewSet, UserHistoryViewSet,get_user_orders, login, create_admin, request_password_reset, verify_reset_code, reset_password
)
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'products', ProductViewSet)
router.register(r'images', ImageViewSet)  # Added ImageViewSet to router
router.register(r'collections', CollectionViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'spinner-rewards', SpinnerRewardViewSet)
router.register(r'spinner-history', UserSpinnerHistoryViewSet, basename='spinner-history')
router.register(r'point-history', PointHistoryViewSet, basename='point-history')
router.register(r'user-history', UserHistoryViewSet, basename='user-history')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/login/', login, name='login'),
    path('api/create-admin/', create_admin, name='create-admin'),
    # Add these new URL patterns for password reset functionality
    path('api/request-password-reset/', request_password_reset, name='request_password_reset'),
    path('api/verify-reset-code/', verify_reset_code, name='verify_reset_code'),
    path('api/reset-password/', reset_password, name='reset_password'),
    path('api/orders/users/<int:user_id>/', get_user_orders, name='user-orders'),

]
# Add this at the end of the file to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)