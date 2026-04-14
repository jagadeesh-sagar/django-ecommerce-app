
from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser

from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly
from django.db.models import Q
from . import models
from . import serializers
from . import tasks

from django.shortcuts import get_object_or_404

from api.authentication import CookieJWTAuthentication

class PaymentView(generics.ListCreateAPIView):
    '''
    Payment API

    Allows Authenticated Buyers to:
        - Record a payment method for an Order
        - List all payment records

    Access:
        Authenticated Buyers only

    Methods:
        GET  - Returns all Payment records
        POST - Creates a new Payment record

    GET Response:
        200 OK - List of Payments
        Example:
        ```json
        [
            {
                "payment_method": "credit_card"
            },
            {
                "payment_method": "upi"
            }
        ]
        ```

    POST Request Body:
        ```json
        {
            "payment_method": "String (cash | online_banking | credit_card | debit_card | upi | wallet | gift_card)"
        }
        ```

        Example:
        ```json
        {
            "payment_method": "upi"
        }
        ```

    POST Response:
        201 CREATED - Payment recorded
        Example:
        ```json
        {
            "payment_method": "upi"
        }
        ```
        400 BAD REQUEST - Validation error
        Example:
        ```json
        {
            "payment_method": [
                "\"crypto\" is not a valid choice."
            ]
        }
        ```

    Note:
        - order, amount, and transaction_id are managed server-side
        - only payment_method is exposed in the serializer
    '''
    permission_classes=[IsBuyer]
    queryset=models.Payment.objects.all()
    serializer_class=serializers.PaymentSerializers

payment_list_create_view=PaymentView.as_view()

    

