from django.db import models
# from django.contrib.auth.models import User
from api.models import User

class Coupon(models.Model):
    DISCOUNT_TYPES=[
      ('percentage','Percentage'),
      ('fixed','Fixed Amount')
    ]
    code=models.CharField(max_length=50,unique=True)
    description=models.TextField(null=True,blank=True)
    discount_type=models.CharField(max_length=20,choices=DISCOUNT_TYPES,default='percentage')
    discount_percent=models.IntegerField(default=0,null=True)
    start_date=models.DateField()
    expiry_date=models.DateField()
    # max_uses=models.IntegerField
    max_uses=models.IntegerField(default=1,null=True)
    used_count=models.IntegerField(default=0)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)


class Offer(models.Model):
      OFFER_TYPES = [
        ('diwali', 'Diwali'),
        ('dussehra', 'Dussehra'),
        ('new_year', 'New Year'),
        ('independence', 'Independence Day'),
        ('republic_day', 'Republic Day'),
        ('bumper_sale', 'Bumper Sale'),
        ('flash_sale', 'Flash Sale'),
    ]
      name=models.CharField(max_length=200)
      product=models.ForeignKey('user.Product',on_delete=models.CASCADE,related_name='offers',null=True,blank=True)
      category=models.ForeignKey('user.Category',on_delete=models.CASCADE,related_name='offers',null=True,blank=True)
      offer_type=models.CharField(max_length=50,choices=OFFER_TYPES,default='bumper_sales')
      discount_type=models.CharField(max_length=20,choices=[
          ('percentage','Percentage'),
          ('fixed','Fixed Amount')
      ],default='percentage')
      discount_value=models.DecimalField(max_digits=10,decimal_places=2)
      start_date=models.DateTimeField()
      end_date=models.DateTimeField()
      is_activve=models.BooleanField(default=True)
    
      def __str__(self):
          return f"{self.name} - {self.offer_type}"


class Banner(models.Model):
    title=models.CharField(max_length=200)
    image_url=models.URLField(max_length=500)
    link_url=models.URLField(max_length=500,null=True,blank=True)
    offer=models.ForeignKey(Offer,on_delete=models.SET_NULL,null=True,blank=True,related_name='banners')
    display_order=models.IntegerField(default=0)
    is_active=models.BooleanField(default=True)
    start_date=models.DateTimeField(null=True,blank=True)
    end_date=models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.title
    
  
class Notification(models.Model):
   NOTIFICATION_TYPES=[
        ('marketing', 'Marketing'),
        ('offer', 'Offer'),
        ('coupon', 'Coupon'),
        ('festive_sale', 'Festive Sale'),
        ('order_update', 'Order Update'),
        ('product_restock', 'Product Restock'),
   ]
   
   user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications')
   notification_type=models.CharField(max_length=200,choices=NOTIFICATION_TYPES,default='offer')
   title=models.CharField(max_length=200)
   message=models.TextField()
   link_url=models.URLField(max_length=500,null=True,blank=True)
   read_status=models.BooleanField(default=False)
   created_at=models.DateTimeField(auto_now_add=True)

   class Meta:
        ordering = ['-created_at']

   def __str__(self):
        return f"{self.notification_type} for {self.user.username}"



