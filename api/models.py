from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES=[
        ('seller','Seller'),
        ('buyer','Buyer'),
        ]
    
    role_model=models.CharField(choices=ROLE_CHOICES,max_length=20,default='buyer')

    def is_buyer(self):
        return self.role=='seller'
    def is_seller(self):
        return self.role=='buyer'