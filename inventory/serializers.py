from api.models import User
from . import models
from rest_framework import serializers

class SellerRegistration(serializers.ModelSerializer):
    class Meta:
        model=models.Seller
        fields=['business_name','gst_number']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if models.Seller.objects.filter(user=request.user).exists():
                raise serializers.ValidationError({"error": "You are already registered as a seller."})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['verified_status'] = True

        # Update the user's role to seller
        if user.role_model != 'seller':
            user.role_model = 'seller'
            user.save()

        return super().create(validated_data)