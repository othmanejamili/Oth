# views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework import permissions, viewsets, filters
from .models import User, Product, Image, Collection, Comment, Order, OrderItem, SpinnerReward, UserSpinnerHistory, PointHistory, UserHistory,PasswordResetCode
from .serializers import (
    UserSerializer, ProductSerializer, ImageSerializer, CollectionSerializer, CommentSerializer,
    OrderSerializer, OrderItemSerializer, SpinnerRewardSerializer, UserSpinnerHistorySerializer,
    PointHistorySerializer, UserHistorySerializer
)
from rest_framework.permissions import IsAuthenticated


###############
# In your views.py file
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetCode  # Make sure this import is present


User = get_user_model()

# Store verification codes temporarily (in production, use a database model)
# Format: {email: {"code": "123456", "created_at": timestamp}}
reset_codes = {}

# Helper function to generate a random code
def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    import logging
    logger = logging.getLogger(__name__)
    
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # We don't want to reveal if a user exists or not for security reasons
            logger.info(f"Password reset requested for non-existent email: {email}")
            return Response({'message': 'If this email is registered, a reset code has been sent'})
        
        # Generate a verification code
        code = generate_verification_code()
        
        # Store code in database
        try:
            PasswordResetCode.objects.create(
                email=email,
                code=code
            )
            logger.info(f"Created password reset code for {email}")
        except Exception as e:
            logger.error(f"Failed to create reset code in database: {str(e)}")
            return Response(
                {'error': 'An error occurred while processing your request'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Send email with verification code
        subject = "Reset Your Password – Verification Code from OJ Company"
        message = (
            f"Hello,\n\n"
            f"You recently requested to reset your password for your OJ Company account.\n"
            f"Your verification code is: "
            f"{code}\n\n"
            f"This code is valid for 10 minutes.\n\n"
            f"If you did not request a password reset, please ignore this message.\n\n"
            f"Best regards,\n"
            f"The OJ Company Team"
        )

        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        
        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            # Even if email fails, don't reveal this to user for security
            
        return Response({'message': 'Password reset code sent to your email'})
        
    except Exception as e:
        logger.error(f"Unexpected error in password reset: {str(e)}")
        return Response(
            {'error': 'An error occurred while processing your request'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code(request):
    """
    Verify that the reset code is valid
    """
    email = request.data.get('email')
    code = request.data.get('code')
    
    if not email or not code:
        return Response(
            {'error': 'Email and verification code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get the most recent code for this email that hasn't been used
        reset_code = PasswordResetCode.objects.filter(
            email=email,
            code=code,
            is_used=False
        ).latest('created_at')
        
        # Check if code is valid using the model method
        if reset_code.is_valid():
            return Response({'message': 'Code verified successfully'})
        else:
            return Response(
                {'error': 'Verification code has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except PasswordResetCode.DoesNotExist:
        return Response(
            {'error': 'Invalid verification code'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset the password using the verified code
    """
    email = request.data.get('email')
    code = request.data.get('code')
    new_password = request.data.get('new_password')
    
    if not email or not code or not new_password:
        return Response(
            {'error': 'Email, verification code, and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get the most recent code for this email that hasn't been used
        reset_code = PasswordResetCode.objects.filter(
            email=email,
            code=code,
            is_used=False
        ).latest('created_at')
        
        # Check if code is valid
        if not reset_code.is_valid():
            return Response(
                {'error': 'Verification code has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update user's password
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Mark code as used
            reset_code.is_used = True
            reset_code.save()
            
            return Response({'message': 'Password has been reset successfully'})
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    except PasswordResetCode.DoesNotExist:
        return Response(
            {'error': 'Invalid verification code'},
            status=status.HTTP_400_BAD_REQUEST
        )
#####################################
# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from Ecomm.models import User  # Import your custom User model
from django.contrib.auth import authenticate

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_admin(request):
    """Only existing admins can create new admins"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not username or not email or not password:
        return Response({'error': 'Please provide username, email and password'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_staff = True  # Make them admin
    user.save()
    
    return Response({'message': f'Admin user {username} created successfully'}, 
                    status=status.HTTP_201_CREATED)


# views.py
from rest_framework.authtoken.models import Token
# Add this to your views.py to debug authentication issues

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Add this to your views.py file

@api_view(['GET'])
@permission_classes([AllowAny])
def api_status(request):
    """
    Simple endpoint to check if the API is online and responding
    """
    return Response({
        'status': 'online',
        'message': 'API is operational',
        'version': '1.0.0'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Enhanced login endpoint with better error handling and debugging
    """
    # Log the incoming request data (excluding password for security)
    safe_data = request.data.copy()
    if 'password' in safe_data:
        safe_data['password'] = '********'
    logger.info(f"Login attempt for user: {safe_data.get('username', 'unknown')}")
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Validate required fields
    if not username or not password:
        logger.warning(f"Login failed - missing credentials for user: {username}")
        return Response(
            {'error': 'Please provide both username and password'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Attempt authentication
    user = authenticate(username=username, password=password)
    
    if user:
        # Authentication successful
        token, created = Token.objects.get_or_create(user=user)
        logger.info(f"Login successful for user: {username}")
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_staff
        })
    else:
        # Authentication failed - try to determine why
        try:
            from Ecomm.models import User
            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                logger.warning(f"Login failed - incorrect password for existing user: {username}")
                error_message = "Invalid credentials - password incorrect"
            else:
                logger.warning(f"Login failed - user does not exist: {username}")
                error_message = "Invalid credentials - user not found"
                
            # For security, don't expose specific details to client
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Error during login process: {str(e)}")
            return Response(
                {'error': 'Server error during authentication'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#####################################

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users with full CRUD operations.
    
    list:
    GET /api/users/ - List all users (admin only)
    
    retrieve:
    GET /api/users/{id}/ - Get specific user (admin or owner)
    
    create:
    POST /api/users/ - Create new user
    
    update:
    PUT /api/users/{id}/ - Update user (admin or owner)
    
    partial_update:
    PATCH /api/users/{id}/ - Partially update user (admin or owner)
    
    destroy:
    DELETE /api/users/{id}/ - Delete user (admin only)
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email','first_name','last_name']
    ordering_fields = ['username', 'date_joined', 'points']
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # Allow users to view and update their own profile
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        GET /api/users/{id}/history/ - Get user history
        """
        user = self.get_object()
        histories = UserHistory.objects.filter(user=user)
        serializer = UserHistorySerializer(histories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def point_history(self, request, pk=None):
        """
        GET /api/users/{id}/point_history/ - Get user point history
        """
        user = self.get_object()
        point_histories = PointHistory.objects.filter(user=user)
        serializer = PointHistorySerializer(point_histories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """
        GET /api/users/{id}/orders/ - Get user orders
        """
        user = self.get_object()
        orders = Order.objects.filter(user=user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """
        GET /api/users/{id}/comments/ - Get user comments
        """
        user = self.get_object()
        comments = Comment.objects.filter(user=user)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'type', 'size']
    ordering_fields = ['name', 'price', 'stock', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Parse include_images query param, defaulting to 'true'
        include_images = self.request.query_params.get('include_images', 'true').lower() == 'true'
        context['include_images'] = include_images
        return context
    
    def create(self, request, *args, **kwargs):
        """
        Create a new product with optional images in a single request
        """
        # Debug what's being received
        print("Request data:", request.data)
        print("Request FILES:", request.FILES)
        
        # Create a separate copy of the data without the files
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data.copy()
        
        # Remove 'images' key from data if it exists to avoid validation errors
        if 'images' in data:
            del data['images']
        
        # Create the serializer with the data (excluding files)
        serializer = self.get_serializer(data=data)
        
        if serializer.is_valid():
            # Create the product first
            product = serializer.save()
            
            # Now handle image uploads separately
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                for image in images:
                    Image.objects.create(
                        product=product,
                        image_url=image
                    )
            
            # Return the complete product with images
            return Response(
                ProductSerializer(product, context=self.get_serializer_context()).data, 
                status=status.HTTP_201_CREATED
            )
        
        # Print validation errors for debugging
        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """
        Update a product with complete replacement of images in a single request
        """
        # Debug what's being received
        print("Update request data:", request.data)
        print("Update request FILES:", request.FILES)
        
        # Get the product instance
        instance = self.get_object()
        
        # Create a separate copy of the data without the files
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data.copy()
        
        # Remove 'images' key from data if it exists to avoid validation errors
        if 'images' in data:
            del data['images']
            
        # Check if we need to replace images
        replace_images = 'images' in request.FILES
        
        if replace_images:
            # Delete all existing images if there are new images
            # This ensures a complete replacement
            instance.images.all().delete()
        # If no 'images' in FILES but 'removed_image_ids' is present, handle selective removal
        elif 'removed_image_ids' in data:
            try:
                # Parse the JSON string containing removed image IDs
                import json
                removed_image_ids = json.loads(data['removed_image_ids'])
                # Delete those images
                for image_id in removed_image_ids:
                    try:
                        image = Image.objects.get(id=image_id, product=instance)
                        image.delete()
                    except Image.DoesNotExist:
                        print(f"Image with ID {image_id} not found")
                # Remove from data to avoid serializer validation errors
                del data['removed_image_ids']
            except json.JSONDecodeError:
                print("Error decoding removed_image_ids JSON")
        
        # Update the product data
        serializer = self.get_serializer(instance, data=data, partial=kwargs.get('partial', False))
        
        if serializer.is_valid():
            # Save the updated product
            product = serializer.save()
            
            # Handle new image uploads
            if replace_images:
                images = request.FILES.getlist('images')
                for image in images:
                    Image.objects.create(
                        product=product,
                        image_url=image
                    )
            
            # Return the complete updated product with images
            return Response(
                ProductSerializer(product, context=self.get_serializer_context()).data
            )
        
        # Print validation errors for debugging
        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """
        GET /api/products/{id}/images/ - Get product images
        """
        product = self.get_object()
        images = product.images.all()
        serializer = ImageSerializer(images, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """
        POST /api/products/{id}/add_image/ - Add image to product (admin only)
        """
        product = self.get_object()
        
        # Check if the request contains a file
        if 'image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a new image instance
        image = Image.objects.create(
            product=product,
            image_url=request.FILES['image']
        )
        
        serializer = ImageSerializer(image)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_image(self, request, pk=None):
        """
        DELETE /api/products/{id}/remove_image/?image_id={image_id} - Remove image from product (admin only)
        """
        product = self.get_object()
        image_id = request.query_params.get('image_id')
        
        if not image_id:
            return Response({'error': 'No image_id provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image = Image.objects.get(id=image_id, product=product)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Image.DoesNotExist:
            return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Other actions remain the same

class ImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product images with full CRUD operations.
    """
    queryset = Image.objects.all().order_by('-uploaded')
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['uploaded']
    
    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """
        GET /api/images/by_product/?product_id={id} - Get images by product
        """
        product_id = request.query_params.get('product_id', None)
        if product_id:
            images = Image.objects.filter(product_id=product_id)
            serializer = self.get_serializer(images, many=True)
            return Response(serializer.data)
        return Response([])

class CollectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for collections with full CRUD operations.
    
    list:
    GET /api/collections/ - List all collections
    
    retrieve:
    GET /api/collections/{id}/ - Get specific collection
    
    create:
    POST /api/collections/ - Create new collection (admin only)
    
    update:
    PUT /api/collections/{id}/ - Update collection (admin only)
    
    partial_update:
    PATCH /api/collections/{id}/ - Partially update collection (admin only)
    
    destroy:
    DELETE /api/collections/{id}/ - Delete collection (admin only)
    """
    queryset = Collection.objects.all().order_by('-created_at')
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """
        GET /api/collections/{id}/products/ - Get collection products
        """
        collection = self.get_object()
        products = collection.products.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        """
        POST /api/collections/{id}/add_product/ - Add product to collection (admin only)
        
        Request body: {"product_id": 1}
        """
        collection = self.get_object()
        product_id = request.data.get('product_id', None)
        
        if not product_id:
            return Response(
                {"error": "Product ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            product = Product.objects.get(id=product_id)
            collection.products.add(product)
            return Response(
                {"success": f"Product '{product.name}' added to collection '{collection.name}'"},
                status=status.HTTP_200_OK
            )
        except Product.DoesNotExist:
            return Response(
                {"error": f"Product with ID {product_id} does not exist"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_product(self, request, pk=None):
        """
        POST /api/collections/{id}/remove_product/ - Remove product from collection (admin only)
        
        Request body: {"product_id": 1}
        """
        collection = self.get_object()
        product_id = request.data.get('product_id', None)
        
        if not product_id:
            return Response(
                {"error": "Product ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            product = Product.objects.get(id=product_id)
            if product in collection.products.all():
                collection.products.remove(product)
                return Response(
                    {"success": f"Product '{product.name}' removed from collection '{collection.name}'"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": f"Product '{product.name}' is not in collection '{collection.name}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Product.DoesNotExist:
            return Response(
                {"error": f"Product with ID {product_id} does not exist"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product comments/reviews with full CRUD operations.
    
    list:
    GET /api/comments/ - List all comments
    
    retrieve:
    GET /api/comments/{id}/ - Get specific comment
    
    create:
    POST /api/comments/ - Create new comment (authenticated users)
    
    update:
    PUT /api/comments/{id}/ - Update comment (owner or admin)
    
    partial_update:
    PATCH /api/comments/{id}/ - Partially update comment (owner or admin)
    
    destroy:
    DELETE /api/comments/{id}/ - Delete comment (owner or admin)
    """
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']
    
    def get_queryset(self):
        queryset = Comment.objects.all()
        
        # Filter by product if specified
        product_id = self.request.query_params.get('product_id', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by user if specified
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        # Create user history entry for comment
        UserHistory.objects.create(
            user=self.request.user,
            action_type='comment_added',
            description=f"Comment added for product {serializer.validated_data['product'].name}"
        )
    
    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        
        # Only allow update by the comment owner or admin
        if request.user != comment.user and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to update this comment"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
        
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        
        # Only allow deletion by the comment owner or admin
        if request.user != comment.user and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to delete this comment"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for orders with full CRUD operations.
    
    list:
    GET /api/orders/ - List all orders (admin) or user's orders
    
    retrieve:
    GET /api/orders/{id}/ - Get specific order (owner or admin)
    
    create:
    POST /api/orders/ - Create new order (authenticated users)
    
    update:
    PUT /api/orders/{id}/ - Update order (admin only)
    
    partial_update:
    PATCH /api/orders/{id}/ - Partially update order (admin only)
    
    destroy:
    DELETE /api/orders/{id}/ - Delete order (admin only)
    """
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_amount', 'status']
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['list', 'retrieve']:
            # Allow authenticated users to list/retrieve their own orders
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only admins can modify orders
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        
        # For retrieve action, check if user can access the specific order
        if self.action == 'retrieve':
            if user.is_staff:
                return Order.objects.all()
            else:
                # Regular users can only retrieve their own orders
                return Order.objects.filter(user=user)
        
        # For list action
        if user.is_staff:
            # Admin can see all orders
            queryset = Order.objects.all()
            
            # Filter by status if specified
            status_param = self.request.query_params.get('status', None)
            if status_param:
                queryset = queryset.filter(status=status_param)
                
            return queryset.order_by('-created_at')
        
        # Regular users can only see their own orders
        return Order.objects.filter(user=user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Check if user is authenticated before assigning to order
        if self.request.user.is_authenticated:
            order = serializer.save(user=self.request.user)
            
            # Create user history entry for order
            UserHistory.objects.create(
                user=self.request.user,
                action_type='order_placed',
                description=f"Order #{order.id} placed"
            )
            
            # Add points to user for purchase
            points_to_add = 0
            for item in order.items.all():
                points_to_add += item.product.points_reward * item.quantity
            
            if points_to_add > 0:
                self.request.user.points += points_to_add
                self.request.user.save()
                
                # Create point history entry
                PointHistory.objects.create(
                    user=self.request.user,
                    points=points_to_add,
                    transaction_type='earned',
                    description=f"Points earned from Order #{order.id}"
                )
        else:
            # Handle guest checkout
            order = serializer.save()  # Don't assign a user
    
    def update(self, request, *args, **kwargs):
        # Only admins can update orders
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can update orders"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
        
    def destroy(self, request, *args, **kwargs):
        # Only admins can delete orders
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can delete orders"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)
class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for order items with full CRUD operations.
    
    list:
    GET /api/order-items/ - List all order items (admin only)
    
    retrieve:
    GET /api/order-items/{id}/ - Get specific order item (owner or admin)
    
    create:
    POST /api/order-items/ - Create new order item (authenticated users or guests with order token)
    
    update:
    PUT /api/order-items/{id}/ - Update order item (admin only)
    
    partial_update:
    PATCH /api/order-items/{id}/ - Partially update order item (admin only)
    
    destroy:
    DELETE /api/order-items/{id}/ - Delete order item (admin only)
    """
    queryset = OrderItem.objects.all().order_by('-created_at')
    serializer_class = OrderItemSerializer
    permission_classes = [AllowAny]  # Changed from IsAuthenticated to AllowAny
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]  # Allow anyone (authenticated or not) to create order items
        elif self.action in ['update', 'partial_update', 'destroy', 'list']:
            return [permissions.IsAdminUser()]
        elif self.action == 'retrieve':
            return [permissions.IsAuthenticated()]  # Must be authenticated to view single items
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return OrderItem.objects.all().order_by('-created_at')
        
        # Regular users can only see items from their own orders
        if user.is_authenticated:
            return OrderItem.objects.filter(order__user=user).order_by('-created_at')
        return OrderItem.objects.none()  # Guest users can't list items
    
    def perform_create(self, serializer):
        order = serializer.validated_data.get('order')
        
        # If user is authenticated, verify they own the order or are admin
        if self.request.user.is_authenticated:
            if self.request.user.is_staff or order.user == self.request.user:
                serializer.save()
            else:
                raise PermissionDenied("You don't have permission to add items to this order")
        else:
            # Guest user - allow adding items to orders with no user assigned
            # Or to orders with matching guest_email if implemented
            if order.user is None:  # This indicates it's a guest order
                serializer.save()
            else:
                raise PermissionDenied("You don't have permission to add items to this order")
            
class SpinnerRewardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for spinner rewards with full CRUD operations.
    
    list:
    GET /api/spinner-rewards/ - List all active spinner rewards
    
    retrieve:
    GET /api/spinner-rewards/{id}/ - Get specific spinner reward
    
    create:
    POST /api/spinner-rewards/ - Create new spinner reward (admin only)
    
    update:
    PUT /api/spinner-rewards/{id}/ - Update spinner reward (admin only)
    
    partial_update:
    PATCH /api/spinner-rewards/{id}/ - Partially update spinner reward (admin only)
    
    destroy:
    DELETE /api/spinner-rewards/{id}/ - Delete spinner reward (admin only)
    """
    queryset = SpinnerReward.objects.filter(is_active=True)
    serializer_class = SpinnerRewardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['points_cost', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def spin(self, request, pk=None):
        """
        POST /api/spinner-rewards/{id}/spin/ - Use spinner reward
        """
        user = request.user
        reward = self.get_object()
        
        # Check if user has enough points
        if user.points < reward.points_cost:
            return Response(
                {"error": "Not enough points to spin"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deduct points from user
        user.points -= reward.points_cost
        user.save()
        
        # Create spinner history
        UserSpinnerHistory.objects.create(
            user=user,
            spinner_reward=reward,
            points_spent=reward.points_cost
        )
        
        # Create point history
        PointHistory.objects.create(
            user=user,
            points=-reward.points_cost,
            transaction_type='spent',
            description=f"Points spent on spinner for {reward.name}"
        )
        
        # Create user history
        UserHistory.objects.create(
            user=user,
            action_type='spinner_used',
            description=f"Used spinner and received {reward.name}"
        )
        
        return Response({
            "success": True,
            "reward": SpinnerRewardSerializer(reward).data,
            "points_remaining": user.points
        })
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        """
        GET /api/spinner-rewards/all/ - Get all spinner rewards (including inactive ones, admin only)
        """
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can view all spinner rewards"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        rewards = SpinnerReward.objects.all()
        serializer = self.get_serializer(rewards, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        POST /api/spinner-rewards/{id}/toggle_active/ - Toggle reward active status (admin only)
        """
        if not request.user.is_staff:
            return Response(
                {"error": "Only administrators can toggle reward status"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        reward = self.get_object()
        reward.is_active = not reward.is_active
        reward.save()
        
        return Response({
            "success": True,
            "is_active": reward.is_active,
            "message": f"Reward '{reward.name}' is now {'active' if reward.is_active else 'inactive'}"
        })

class UserSpinnerHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user spinner history (read-only).
    
    list:
    GET /api/spinner-history/ - List spinner history for the current user (or all for admin)
    
    retrieve:
    GET /api/spinner-history/{id}/ - Get specific spinner history record
    """
    serializer_class = UserSpinnerHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin can see specific user's history if requested
            user_id = self.request.query_params.get('user_id', None)
            if user_id:
                return UserSpinnerHistory.objects.filter(user_id=user_id).order_by('-created_at')
            return UserSpinnerHistory.objects.all().order_by('-created_at')
        return UserSpinnerHistory.objects.filter(user=user).order_by('-created_at')

class PointHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for point history (read-only).
    
    list:
    GET /api/point-history/ - List point history for the current user (or all for admin)
    
    retrieve:
    GET /api/point-history/{id}/ - Get specific point history record
    """
    serializer_class = PointHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin can see specific user's history if requested
# Admin can see specific user's history if requested
            user_id = self.request.query_params.get('user_id', None)
            if user_id:
                return PointHistory.objects.filter(user_id=user_id).order_by('-created_at')
            return PointHistory.objects.all().order_by('-created_at')
        
        # Regular users can only see their own point history
        return PointHistory.objects.filter(user=user).order_by('-created_at')

class UserHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user activity history (read-only).
    
    list:
    GET /api/user-history/ - List activity history for the current user (or all for admin)
    
    retrieve:
    GET /api/user-history/{id}/ - Get specific activity history record
    """
    serializer_class = UserHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin can see specific user's history if requested
            user_id = self.request.query_params.get('user_id', None)
            if user_id:
                return UserHistory.objects.filter(user_id=user_id).order_by('-created_at')
            return UserHistory.objects.all().order_by('-created_at')
        
        # Regular users can only see their own history
        return UserHistory.objects.filter(user=user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def by_action_type(self, request):
        """
        GET /api/user-history/by_action_type/?action_type={type} - Get history filtered by action type
        """
        action_type = request.query_params.get('action_type', None)
        if not action_type:
            return Response(
                {"error": "Action type parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(action_type=action_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        GET /api/user-history/recent/?limit={number} - Get most recent history entries
        """
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        queryset = self.get_queryset()[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/user-history/summary/ - Get summary of user activity history
        """
        queryset = self.get_queryset()
        
        # Group by action type and count
        from django.db.models import Count
        summary = queryset.values('action_type').annotate(count=Count('action_type'))
        
        return Response(summary)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_orders(request, user_id):
    try:
        # Make sure user can only access their own orders (or admin can access any)
        if request.user.id != user_id and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=403)
            
        orders = Order.objects.filter(user_id=user_id).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)