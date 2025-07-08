from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, PointHistory, UserHistory

@receiver(post_save, sender=Order)
def award_points_on_order(sender, instance, created, **kwargs):
    """
    Award points to user when order status changes to processing, shipped, or delivered
    """
    # Only award points for registered users, not guests
    if not instance.user:
        return
    
    # Award points when order is confirmed (processing, shipped, or delivered)
    if instance.status in ['processing', 'shipped', 'delivered']:
        # Check if points have already been awarded for this order
        existing_point_record = PointHistory.objects.filter(
            user=instance.user,
            description=f'Points earned from Order #{instance.id}'
        ).exists()
        
        if not existing_point_record:
            total_points = 0
            
            # Calculate total points from all items in the order
            for item in instance.items.all():
                product_points = item.product.points_reward * item.quantity
                total_points += product_points
            
            if total_points > 0:
                # Add points to user's account
                instance.user.points += total_points
                instance.user.save()
                
                # Create point history record
                PointHistory.objects.create(
                    user=instance.user,
                    points=total_points,
                    transaction_type='earned',
                    description=f'Points earned from Order #{instance.id}'
                )
                
                # Create user history record
                UserHistory.objects.create(
                    user=instance.user,
                    action_type='order_placed',
                    description=f'Earned {total_points} points from order #{instance.id}'
                )

# Don't forget to import this in your apps.py
# In your apps.py file:
"""
from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'your_app_name'
    
    def ready(self):
        import your_app_name.signals
"""