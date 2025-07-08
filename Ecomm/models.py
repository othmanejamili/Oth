from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta


# User model extending Django's AbstractUser
class User(AbstractUser):
    points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Corrected field

    def __str__(self):
        return self.username


class PasswordResetCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        # Check if code is not used and not expired (10 minutes)
        return (not self.is_used and 
                timezone.now() < self.created_at + timedelta(minutes=10))
    
    def __str__(self):
        return f"Reset code for {self.email}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset Code'
        verbose_name_plural = 'Password Reset Codes'

# Product model
class Product(models.Model):
    name = models.CharField(max_length=365)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField(default=0)
    points_reward = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=265)
    size = models.CharField(max_length=265)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Image model
class Image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='product_images/')  
    uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name} uploaded on {self.uploaded.strftime('%Y-%m-%d %H:%M:%S')}"

# Collection model
class Collection(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    products = models.ManyToManyField(Product, related_name='collections')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Comment/Review model
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

# Order model
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    guest_email = models.EmailField(null=True, blank=True)
    guest_phone_numbre = models.CharField(max_length=15, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    city = models.CharField(max_length=25, blank=False, null=False, default= "No city provided")
    region = models.CharField(max_length=25, blank=False, null=False, default= "No city provided")
    address = models.TextField(default= "No address provided" )  
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Order #{self.id} by {self.user.username}"
        return f"Order #{self.id} by Guest ({self.guest_email})"
    
    def save(self, *args, **kwargs):
        # Ensure either user or guest_email is provided
        if not self.user and not self.guest_email:
            raise ValueError("Either user or guest_email must be provided")
        super().save(*args, **kwargs)

# Order Item model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"

# Spinner Reward model
class SpinnerReward(models.Model):
    REWARD_TYPES = [
        ('discount', 'Discount'),
        ('free_product', 'Free Product'),
        ('bonus_points', 'Bonus Points'),
    ]
    
    name = models.CharField(max_length=100)
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)  # Percentage for discounts, product_id for free products, amount for bonus points
    points_cost = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.reward_type})"

# User Spinner History model
class UserSpinnerHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spinner_history')
    spinner_reward = models.ForeignKey(SpinnerReward, on_delete=models.PROTECT, related_name='user_spins')
    points_spent = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} received {self.spinner_reward.name} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

# Point History model
class PointHistory(models.Model):
    TRANSACTION_TYPES = [
        ('earned', 'Earned'),
        ('spent', 'Spent'),
        ('reward', 'Reward'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_history')
    points = models.IntegerField()  # Can be positive (earned) or negative (spent)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.transaction_type} {abs(self.points)} points"

# User History model
class UserHistory(models.Model):
    ACTION_TYPES = [
        ('registration', 'Registration'),
        ('login', 'Login'),
        ('order_placed', 'Order Placed'),
        ('spinner_used', 'Spinner Used'),
        ('comment_added', 'Comment Added'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"