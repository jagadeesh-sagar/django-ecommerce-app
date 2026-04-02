from django.db import models
# from django.contrib.auth.models import User
from api.models import User
from django.core.validators import MinValueValidator,MaxValueValidator

class Seller(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='seller_profile')
    business_name=models.CharField(max_length=200)
    gst_number=models.CharField(max_length=15,unique=True)
    verified_status=models.BooleanField(default=False)
    # rating=models.FloatField(default=0.0,validators=[MinValueValidator(0),MaxValueValidator(5)])
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name
  

class Inventory(models.Model):
    product_variant=models.OneToOneField("user.ProductVariant", on_delete=models.CASCADE, related_name='inventory')
    available_stock=models.IntegerField(default=0)
    reserved_stock=models.IntegerField(default=0)  
    low_stock_threshold=models.IntegerField(default=10)
    warehouse_location=models.CharField(max_length=200, null=True, blank=True)
    last_restocked=models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Inventory: {self.product_variant}"
    
    @property
    def total_stock(self):
        return self.available_stock + self.reserved_stock
    
    @property
    def is_low_stock(self):
        return self.available_stock <= self.low_stock_threshold

class InventoryLog(models.Model):
  
    CHANGE_TYPES = [
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('damage', 'Damage'),
        ('adjustment', 'Adjustment'),
        ('reserved', 'Reserved'),
        ('released', 'Released'),
    ]
    
    product_variant=models.ForeignKey("user.ProductVariant", on_delete=models.CASCADE, related_name='inventory_logs')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    quantity_change = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reason = models.TextField(null=True, blank=True)
    reference_id = models.CharField(max_length=100, null=True, blank=True)  
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.change_type} - {self.quantity_change} units"


