from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser
from rest_framework.pagination import LimitOffsetPagination,CursorPagination,PageNumberPagination

from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly,IsOrderParticipant
from . import models
from inventory.models import Seller
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
            .prefetch_related('items','items__product','items__product_variant')
    
        paginator=StandardPagination()
        result_page=paginator.paginate_queryset(queryset,request)

        serializer=serializers.OrderReadSerializers(result_page,many=True,context={"request":request})
        return paginator.get_paginated_response(serializer.data)

order_list_create_view=OrderView.as_view()


class SellerOrderListView(APIView):
    permission_classes = [IsSeller]

    def get(self, request):
        seller_name=Seller.objects.get(user=self.request.user)
        queryset = (
            models.Order.objects
            .filter(items__product__seller=seller_name)
            .distinct()
            .select_related('shipping_address', 'user')
            .prefetch_related('items', 'items__product', 'items__product_variant')
            .order_by('-order_date')
        )
        paginator = StandardPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = serializers.SellerOrderSerializer(
            result_page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

seller_order_list_view = SellerOrderListView.as_view()


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        '''
        Update the status of an order
        
        Request Body:
        ```json
        {
            "status": "delivered"
        }
        ```
        '''
        order = get_object_or_404(models.Order, id=pk)
        
        # Verify user is either the order owner (buyer) or the seller of items in the order or admin
        is_buyer = order.user == request.user
        
        is_seller = False
        try:
            seller_name = Seller.objects.get(user=request.user)
            is_seller = order.items.filter(product__seller=seller_name).exists()
        except Seller.DoesNotExist:
            pass
            
        if not (is_buyer or is_seller or request.user.is_staff):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
        new_status = request.data.get('status')
        valid_statuses = [choice[0] for choice in models.Order.ORDER_STATUS]
        
        if not new_status or new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        order.status = new_status
        order.save()
        
        # Log to OrderStatusHistory
        models.OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=f"Updated to {new_status} via status update API",
            changed_by=request.user
        )
        
        serializer = serializers.OrderReadSerializers(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

order_status_update_view = OrderStatusUpdateView.as_view()
