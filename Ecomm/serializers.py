# serializers.py
from rest_framework import serializers
from .models import User, Product, Image, Collection, Comment, Order, OrderItem, SpinnerReward, UserSpinnerHistory, PointHistory, UserHistory
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 
            'first_name', 'last_name', 'phone_number',
            'points', 'created_at', 'updated_at'
        ]
        read_only_fields = ['points', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # 🔐 Hash the password
        user.save()
        return user


class ImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='image_url', required=False)
    
    class Meta:
        model = Image
        fields = ['id', 'product', 'image', 'uploaded']
        read_only_fields = ['id', 'uploaded']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Only include product ID to avoid circular reference when nested
        if 'product' in representation and isinstance(representation['product'], dict):
            representation['product'] = instance.product.id
        return representation


class ProductSerializer(serializers.ModelSerializer):
    # Make this field not required, as we'll handle files separately
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
        allow_null=True
    )
    image_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'points_reward',
                  'type', 'size', 'created_at', 'updated_at', 'images', 'image_list']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        """
        Validate that price is a positive value
        """
        if value <= Decimal('0'):
            raise serializers.ValidationError("Price must be a positive number")
        return value

    def get_image_list(self, obj):
        # Only include images if requested in the context
        include_images = self.context.get('include_images', True)
        if not include_images:
            return []
        
        images = obj.images.all()
        return ImageSerializer(images, many=True, context=self.context).data

    def create(self, validated_data):
        # Extract images if present, but don't fail if they're not
        images_data = validated_data.pop('images', [])
        
        # Set defaults for fields that might be missing
        if 'stock' not in validated_data:
            validated_data['stock'] = 0
        if 'points_reward' not in validated_data:
            validated_data['points_reward'] = 0
        
        # Create the product first
        product = Product.objects.create(**validated_data)
        
        # Then create images for the product if there are any
        for image_data in images_data:
            if image_data:  # Skip None values
                Image.objects.create(
                    product=product,
                    image_url=image_data
                )
        
        return product


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'name', 'description', 'products', 'created_at']
        read_only_fields = ['created_at']


class CommentSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField(read_only=True)
    product_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'product', 'content', 'rating', 'created_at', 'user_details', 'product_details']
        read_only_fields = ['created_at', 'user_details', 'product_details']
    
    def get_user_details(self, obj):
        """Return user details for the comment"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name
            }
        return None
    
    def get_product_details(self, obj):
        """Return basic product details for the comment"""
        if obj.product:
            return {
                'id': obj.product.id,
                'name': obj.product.name
            }
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    # For write operations - accept product ID
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    
    # For read operations - include full product details
    product_details = ProductSerializer(
        source='product',
        read_only=True,
        context={'include_images': False}  # Don't include images in order items by default
    )
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product_id', 'product_details', 'quantity', 'price_at_purchase', 'created_at']
        # Keep price_at_purchase as read_only since we'll set it automatically
        read_only_fields = ['id', 'created_at', 'price_at_purchase']
    
    def create(self, validated_data):
        """Override create to automatically set price_at_purchase from the product's current price"""
        product = validated_data['product']
        # Always use the current product price to prevent price manipulation
        validated_data['price_at_purchase'] = product.price
        return super().create(validated_data)
    
    def validate_quantity(self, value):
        """Validate that quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_details = serializers.SerializerMethodField(read_only=True)
    customer_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id','customer_name', 'items','user_details','user','guest_email','guest_phone_numbre','total_amount',
            'status','city','region','address','note','created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_details(self, obj):
        """Return user details if user exists"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'phone_number': obj.user.phone_number
            }
        return None
    
    def get_customer_name(self, obj):
        """Generate customer name with fallback options"""
        if not obj.user:
            # For guest orders, use guest email or phone
            return obj.guest_email or obj.guest_phone_number or 'Guest'
        
        # For registered users, prioritize full name
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        
        # Fallback options
        return (
            obj.user.first_name or 
            obj.user.last_name or 
            obj.user.username or 
            obj.user.email or 
            'Unknown User'
        )
    
    def get_total_amount(self, obj):
        """Calculate total amount from order items"""
        return sum(item.quantity * item.price_at_purchase for item in obj.items.all())


class SpinnerRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpinnerReward
        fields = ['id', 'name', 'reward_type', 'value', 'points_cost', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_points_cost(self, value):
        """Validate that points cost is not negative"""
        if value < 0:
            raise serializers.ValidationError("Points cost cannot be negative")
        return value
    
    def validate_value(self, value):
        """Validate that value is positive for applicable reward types"""
        if value <= 0:
            raise serializers.ValidationError("Reward value must be positive")
        return value


class UserSpinnerHistorySerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField(read_only=True)
    reward_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserSpinnerHistory
        fields = ['id', 'user', 'spinner_reward', 'points_spent', 'created_at', 'user_details', 'reward_details']
        read_only_fields = ['id', 'created_at', 'points_spent']
    
    def get_user_details(self, obj):
        """Return basic user details"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None
    
    def get_reward_details(self, obj):
        """Return spinner reward details"""
        if obj.spinner_reward:
            return {
                'id': obj.spinner_reward.id,
                'name': obj.spinner_reward.name,
                'reward_type': obj.spinner_reward.reward_type,
                'value': obj.spinner_reward.value
            }
        return None


class PointHistorySerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = PointHistory
        fields = ['id', 'user', 'points', 'transaction_type', 'description', 'created_at', 'user_details']
        read_only_fields = ['id', 'created_at']
    
    def get_user_details(self, obj):
        """Return basic user details"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None
    
    def validate_points(self, value):
        """Validate points value based on transaction type"""
        # You might want to add specific validation based on transaction_type
        if value == 0:
            raise serializers.ValidationError("Points value cannot be zero")
        return value


class UserHistorySerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserHistory
        fields = ['id', 'user', 'action_type', 'description', 'created_at', 'user_details']
        read_only_fields = ['id', 'created_at']
    
    def get_user_details(self, obj):
        """Return basic user details"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None