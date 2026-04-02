# from django.contrib.auth.models import User
from .models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password


class Userserializer(serializers.ModelSerializer):

    class Meta:
        model=User
        fields=["id","username"]

class UserRegistrationSerializer(serializers.ModelSerializer):

    password=serializers.CharField(write_only=True,validators=[validate_password])
    confirm_password=serializers.CharField(write_only=True)
    role_model=serializers.ChoiceField(choices=['seller','buyer'])

    class Meta:
        model=User
        fields=['username','first_name','last_name','role_model','email','password','confirm_password']

    def validate(self,attrs):
        if attrs['password']!=attrs['confirm_password']:
            raise serializers.ValidationError('Passwords does not maatch')
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError('Usrname already exists')
        
        return attrs
    
    def create(self, validated_data):

        user = User.objects.create_user(
        username=validated_data['username'],
        first_name=validated_data.get('first_name', ''),
        last_name=validated_data.get('last_name', ''),
        email=validated_data['email'],
        password=validated_data['password'],
        role_model=validated_data['role_model']
    )
        return user
