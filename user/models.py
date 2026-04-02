from django.db import models
# from django.contrib.auth.models import User
from api.models import User
from django.core.validators import MinValueValidator,MaxValueValidator

class UserProfile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    full_name=models.CharField(max_length=200)
    date_joined=models.DateTimeField(auto_now_add=True)
    dob=models.DateField(null=True,blank=True)
    loyality_points=models.IntegerField(default=0)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
      
    def __str__(self):
        return self.full_name


class Address(models.Model):
    ADDRESS_TYPES=[

      ('shipping','Shipping'),
      ('billing','Billing'),
      ('both','Both'),
    ]

    user=models.ForeignKey(User,on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='both')
    house_no=models.CharField(max_length=200,null=True,blank=True)
    street = models.CharField(max_length=200, null=True, blank=True)
    city=models.CharField(max_length=200)
    state=models.CharField(max_length=200)
    country=models.CharField(max_length=200)
    postal_code=models.IntegerField(default=0)
    phone_number=models.CharField(max_length=15)
    other_number=models.IntegerField(null=True,blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Addresses"
    
    def __str__(self):
        return f"{self.house_no}, {self.city}"


class Category(models.Model):
    name=models.CharField(max_length=200,unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    origin=models.CharField(max_length=200,null=True,blank=True)
    description=models.TextField(max_length=200,null=True,blank=True)
    is_active = models.BooleanField(default=True)  

    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Brand(models.Model):
    name=models.CharField(max_length=200,unique=True)
    logo=models.URLField(max_length=200,null=True,blank=True)
    description=models.TextField(null=True,blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
          return self.name


class Product(models.Model):
    seller = models.ForeignKey('inventory.Seller', on_delete=models.CASCADE)
    name=models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    base_price=models.DecimalField(max_digits=10,decimal_places=2,null=False)
    category=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    stock_qty=models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
          return f'{self.name}'


class ProductVariant(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE, related_name='variants')
    color=models.CharField(max_length=50,null=True,blank=True)
    size=models.CharField(max_length=50,null=True,blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    stock_qty=models.IntegerField(default=0)
    sku=models.CharField(max_length=100,unique=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        unique_together = ['product', 'color', 'size']
    
    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"


class ProductImage(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')
    image_url=models.URLField(max_length=200)
    alt_text = models.CharField(max_length=200, null=True, blank=True)
    video_url=models.URLField(max_length=200,null=True,blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    def __str__(self):
          return f"Image for {self.product.name}"
  

class Review(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='reviews')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text=models.TextField(null=True,blank=True)
    review_image=models.URLField(max_length=500,null=True,blank=True)
    review_video=models.URLField(max_length=500,null=True,blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'product']
      
    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"


class QnA(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE, related_name='questions')
    product=models.ForeignKey(Product,on_delete=models.CASCADE, related_name='questions')
    question=models.TextField()
    answer=models.TextField(null=True,blank=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answers')
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Q: {self.question[:50]}"


class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=False,related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart of {self.user}"


class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    product_variant=models.ForeignKey(ProductVariant,on_delete=models.SET_NULL,null=True,blank=True)
    quantity=models.IntegerField(default=1,validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product_variant']
    
    def __str__(self):
        return f"{self.quantity} x {self.product_variant}"


class Whishlist(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='wishlist')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.username}'s wishlist item"


class Order(models.Model):
    
    ORDER_STATUS = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
    ('returned', 'Returned')
      ]
    
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='orders')
    order_number = models.CharField(max_length=100, unique=True)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    coupon = models.ForeignKey("marketing.Coupon", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')

    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    product_variant=models.ForeignKey(ProductVariant,blank=True,null=True,on_delete=models.SET_NULL)
    quantity=models.IntegerField(default=1,validators=[MinValueValidator(1)])
    unit_price=models.DecimalField(max_digits=10,decimal_places=2)
    total_price=models.DecimalField(max_digits=10,decimal_places=2)
    discount_applied=models.DecimalField(max_digits=109,decimal_places=2,default=0)

    def __str__(self):
        return f"{self.quantity} x {self.product_variant}"


class OrderStatusHistory(models.Model):
  
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    notes = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']


class Shipment(models.Model):
    SHIPMENT_STATUS = [
        ('preparing', 'Preparing'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('exception', 'Exception'),
        ('returned', 'Returned')
    ]
    
    order=models.OneToOneField(Order,on_delete=models.CASCADE,related_name="shipment")
    tracking_number=models.CharField(max_length=200,unique=True)
    carrier=models.CharField(max_length=100,null=True,blank=True)
    status=models.CharField(max_length=200,choices=SHIPMENT_STATUS, default="preparing")
    shipped_at=models.DateTimeField(null=True,blank=True)
    estimated_delivery=models.DateTimeField(null=True,blank=True)
    delivered_at=models.DateTimeField(null=True,blank=True)
    notes=models.TextField(null=True,blank=True)

    def __str__(self):
        return f"Shipment {self.tracking_number}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash on Delivery'),
        ('online_banking', 'Online Banking'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
        ('gift_card', 'Gift Card')
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='cash')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=200, null=True, blank=True, unique=True)
    payment_gateway = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for Order {self.order.order_number}"