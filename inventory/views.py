from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from . import serializers
from . import models
from rest_framework.response import Response
from rest_framework import status


class SellerRegister(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        queryset=models.Seller.objects.filter(user=self.request.user)
        if not queryset.exists():
            return Response({"error": "Seller not registered"}, status=status.HTTP_404_NOT_FOUND)
        serializer=serializers.SellerRegistration(queryset,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request):
        serializer=serializers.SellerRegistration(data=request.data,
                                                  context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
SellerRegister_view=SellerRegister.as_view()