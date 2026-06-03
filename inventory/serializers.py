from api.models import User
import models
from rest_framework import serializers

class SellerRegistration(serializers.ModelSerializer):
    class Meta:
        model=models.Seller
        fields=['business_name','gst_number']

    def create(self, validated_data):
        validated_data['user']=self.context['request'].user
        validated_data['verified_status']=True

        return super().create(validated_data)