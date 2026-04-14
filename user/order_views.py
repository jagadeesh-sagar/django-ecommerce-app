from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser
from rest_framework.pagination import LimitOffsetPagination,CursorPagination,PageNumberPagination

from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly
from . import models
from . import serializers
from . import tasks
from api.pagination import StandardPagination,LimitOffsetPagination,ProductCursorPagination
from api.authentication import CookieJWTAuthentication

from django.shortcuts import get_object_or_404
from django.db.models import Q




class OrderView(APIView):

    '''
    Allows Authenticated customers to:
        - Order Products 
        - View Orders
    '''
    permission_classes=[IsBuyer]

    def post(self,request):
         '''
         Place a new Order

         Request Body:
         ```json
         {
             "shipping_address": "Integer (Address ID)",
             "billing_address": "Integer (Address ID)",
             "coupon": "Integer (Coupon ID - Optional/null)",
             "items": [
                 {
                     "product": "Integer (Product ID)",
                     "product_variant": "Integer (Variant ID - Optional)",
                     "quantity": "Integer"
                 }
             ]
         }
         ```

         Example:
         ```json
         {
             "shipping_address": 1,
             "billing_address": 1,
             "coupon": null,
             "items": [
                 {
                     "product": 1,
                     "product_variant": 12,
                     "quantity": 2
                 }
             ]
         }
         ```

         Note:
             - coupon applies a 10% discount on subtotal
             - tax is calculated at 18% of subtotal
             - total_amount = subtotal + tax_amount - discount_amount

         Responses:
             201 CREATED : Order placed
             Example:
             ```json
             {
                 "shipping_address": 1,
                 "billing_address": 1,
                 "coupon": null,
                 "items": [
                     {
                         "product": 1,
                         "product_name": "samsung s23",
                         "product_variant": 12,
                         "quantity": 2
                     }
                 ]
             }
             ```
             400 BAD REQUEST : Validation error
         '''
         serializer=serializers.OrderSerializer(data=request.data,context={'request':request})
         if serializer.is_valid():
             serializer.save()
             return Response(serializer.data,status=status.HTTP_201_CREATED)
         return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def get(self,request):
        '''
        Returns all Orders placed by the authenticated user

        Access:
            Authenticated

        Response:
            200 OK - List of Orders
            Example:
            ```json
            [
                {
                    "items": [
                        {
                            "product": 1,
                            "product_name": "samsung s23",
                            "product_variant": 12,
                            "quantity": 2
                        }
                    ],
                    "shipping_address": {
                        "user": "jaggu",
                        "address_type": "both",
                        "house_no": "Plot No. 42, Green Villas",
                        "street": "Madhapur Main Road",
                        "city": "Hyderabad",
                        "state": "Telangana",
                        "country": "India",
                        "postal_code": 500081,
                        "phone_number": "+919876543210",
                        "other_number": null
                    },
                    "billing_address": {
                        "user": "jaggu",
                        "address_type": "both",
                        "house_no": "Plot No. 42, Green Villas",
                        "street": "Madhapur Main Road",
                        "city": "Hyderabad",
                        "state": "Telangana",
                        "country": "India",
                        "postal_code": 500081,
                        "phone_number": "+919876543210",
                        "other_number": null
                    },
                    "subtotal": "40000.00",
                    "discount_amount": "0.00",
                    "shipping_cost": "0.00",
                    "tax_amount": "7200.00",
                    "total_amount": "47200.00",
                    "coupon": null,
                    "status": "pending",
                    "order_date": "2026-04-10T10:30:00Z"
                }
            ]
            ```
        '''
        queryset=models.Order.objects \
            .filter(user=self.request.user) \
            .select_related('shipping_address','billing_address')\
            .prefetch_related('items','items__product,items__product_variant')

        paginator=StandardPagination()
        result_page=paginator.paginate_queryset(queryset,request)

        serializer=serializers.OrderReadSerializers(result_page,many=True,context={"request":request})
        return paginator.get_paginated_response(serializer.data)

order_list_create_view=OrderView.as_view()
