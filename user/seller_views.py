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

from inventory.models import Seller
from django.shortcuts import get_object_or_404
from django.db.models import Q


class SellerAnswers(APIView):
    '''
    SellerQnAAnswers API

    Allows verified and Authenticated Sellers to:
        - Answer to the Customer Questions
    
    Method:
        -GET
        -POST

    '''
    permission_classes=[IsSeller,IsProductOwner]

    def get_queryset(self):
        
        try:
            # finds seller and all his Products QnA
            seller=Seller.objects.get(user=self.request.user)
            return models.QnA.objects.filter(product__seller=seller)
        except Seller.DoesNotExist:
           return models.QnA.objects.none()

    def get(self,request,*args,**kwargs):
        '''
        Returns the Answer of the Seller

        :param kwargs:Index of QnA(id)

        Response:
            200 OK : Returned Seller Answer
            Example:
            ```Json
            {
                "id": 1,
                "answer": null,
                "product": 1,
                "question": "is battery have a warrant"
            }       
            ```
        '''
        pk=kwargs['pk']
        #returns the Qna object if Exists 
        question=get_object_or_404(self.get_queryset(),id=pk)
        serializer=serializers.SellerAnswersSerializers(question,context={'request':request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def patch(self,request,*args,**kwargs):
        '''
        Seller can Answer for customer questions

        Response:
            200 OK : saves sellers answer
            400 BAD REQUEST: validation Error
        
        request body:
        Example:
        ```json
        {
        "id": 1,
        "answer": "haa it have 2 years warrant",
        "product": 1,
        "question": "is battery have a warrant"
        }        
        ```
        :param kwargs: question id
        '''
        pk=kwargs['pk']
        question=get_object_or_404(self.get_queryset(),id=pk)
        serializer=serializers.SellerAnswersSerializers(question,data=request.data,partial=True,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

seller_ans_view=SellerAnswers.as_view()


