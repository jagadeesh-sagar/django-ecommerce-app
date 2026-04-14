from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser
from rest_framework.pagination import LimitOffsetPagination,CursorPagination,PageNumberPagination

from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly
from . import models
from . import serializers
from api.pagination import StandardPagination,LimitOffsetPagination,ProductCursorPagination
from . import tasks

from api.models import User
from inventory.models import Seller
from django.shortcuts import get_object_or_404
from django.db.models import Q

import boto3
from django.conf import settings

from api.authentication import CookieJWTAuthentication


class ProductsListAPIView(APIView):
    '''
    Products List API

    Allows all users (Aunthenticated or not) to:
       - List all available Products 
        
    '''

    def get(self, request):
        '''
        Retrieve all available products

        Access:
            public
        Response:
            200 ok -List of products
            ```json
            [
                {
                    "product_name": "samsung s23",
                    "description": "good phone",
                    "category_name": "phones",
                    "base_price": "20000.00",
                    "brand_name": "samsung",
                    "product_detail": "http://127.0.0.1:8000/user/product/detail/1"
                }
            ]
            ```  
        '''
        queryset=models.Product.objects.select_related(
            'category', 'brand'
        )
        
        paginator = StandardPagination()
        result_page = paginator.paginate_queryset(queryset, request)
   
        serializer = serializers.ProductSerializer(result_page, many=True, context={'request': request}) 
        return paginator.get_paginated_response(serializer.data)

product_list_view=ProductsListAPIView.as_view()


class ProductDetailView(mixins.RetrieveModelMixin,generics.GenericAPIView):
    '''
     Product Detail API
     
     Allows all Users(Authenticated or not) to:
     - List details of a Product

    '''
    # authentication_classes = [CookieJWTAuthentication] 
    permission_classes=[AllowAny]
  

    queryset=models.Product.objects\
    .select_related('category','brand','seller__user') \
    .prefetch_related('images','variants','reviews','questions')

    serializer_class=serializers.ProductDetailSerializers
    lookup_field='pk'

    def get(self,request,*args,**kwargs):
        '''
        Returns the details of a Product using:
            :param args: Product ID

        Access:
            public
        Response:
            200 ok -details of a Product 
            Example:
            ```json
        {
            "seller_name": "jaggu",
            "images": [
                {
                    "image_url": "https://rukminim2.flixcart.com/image/300/300/xif0q/mobile/t/0/g/-original-imah4zp7fvqp8wev.jpeg",
                    "alt_text": "s23",
                    "video_url": null,
                    "is_primary": true,
                    "display_order": 0
                }
            ],
            "product_name": "samsung s23",
            "category_name": "phones",
            "description": "good phone",
            "base_price": "20000.00",
            "brand_name": "samsung",
            "stock_qty": 0,
            "sku": "20",
            "is_active": true,
            "variants": [
                {
                    "id": 12,
                    "color": "blue",
                    "size": "pro max",
                    "price": "123455.00",
                    "stock_qty": 122,
                    "sku": "df42ed3111"
                }
            ],
            "reviews": [
                {
                    "rating": 4,
                    "review_text": "good",
                    "review_image": "",
                    "review_video": "",
                    "is_verified_purchase": true
                },
                {
                    "rating": 4,
                    "review_text": "good rey",
                    "review_image": "",
                    "review_video": "",
                    "is_verified_purchase": true
                }
            ],
            "new_review": "http://127.0.0.1:8000/user/product/detail/review/?q=1",
            "questions": [
                {
                    "question": "is battery works well",
                    "answer": "it wonr",
                    "endpoint": "http://127.0.0.1:8000/user/product/seller-ans/1"
                }
                ],
            "new_question": "http://127.0.0.1:8000/user/product/customer-qxn/?q=1",
            "whishlist": "http://127.0.0.1:8000/user/whishlist/?q=1"
        }
            ```
        '''
        
        # print("AUTH CLASS:",self.request.successful_authenticator)
        # print("COOKIES:",self.request.COOKIES)
        return self.retrieve(request,*args,**kwargs)
    
    
product_detail_view=ProductDetailView.as_view()


class ProductSearch(APIView):
     '''
     Product Search API

     Allows all users (Aunthenticated or not) to:

        Filters all available products based on:
        - category
        - Name
        - Brand
        - Price range

     Query parameters:
        ct : Category name
        n  : Product(partial match)
        b  : Brand
        p  : Approximate Price 
        
     Note:
        Price search includes ±1000 range

     '''
     queryset=models.Product.objects \
        .select_related('category','brand','seller__user')\
        .prefetch_related('variants').all()
     
     permission_classes=[AllowAny] 

     def get_queryset(self):
         return models.Product.objects \
        .select_related('category','brand','seller__user')\
        .prefetch_related('variants').all()
       
        
     def get(self,request):
        '''
        Filters available products using Query paramters

        Default:
            - returns all available Products
        Access:
            public 
        Response:
            200 ok -List of products
            Example:
            ```json
        [
            {
                "product_name": "samsung s23",
                "description": "good phone",
                "category_name": "phones",
                "base_price": "20000.00",
                "brand_name": "samsung",
                "product_detail": "http://127.0.0.1:8000/user/product/detail/1"
            }
        ]  
            ```
        '''
        category=request.query_params.get('ct',None)
        name=self.request.GET.get('n',None)
        brand=self.request.GET.get('b',None)
        price=request.query_params.get('price')
        print(price)
       
        queryset=self.get_queryset()

        if category:
            queryset=queryset.filter(Q(category__name__icontains=category)) 

        if name:
            queryset=queryset.filter(Q(name__icontains=name)) 

        if brand:
            queryset=queryset.filter(Q(brand__name__icontains=brand)) 

        if price :
            try:
                value = max(0, min(int(price), 1000000))
                min_p=max(0,value-1000)
                max_p=value+1000
                queryset = queryset.filter(base_price__range=(min_p, max_p))

            except (ValueError, TypeError):  
                return Response({"error": "Invalid price"}, status=400)

        paginator=StandardPagination()
        result_page=paginator.paginate_queryset(queryset,request)

        serializer=serializers.ProductSearchSerializers(result_page,many=True,context={'request':request})

        return paginator.get_paginated_response(serializer.data)
product_search_view=ProductSearch.as_view()


class ProductImageListview(APIView):
    '''
     Product Image API

     Allows Authenticated and Verified Sellers to:
        - Upload images and videos of Products
        - AWS S3 Presigned urls are used to Upload
        
     Workflow:
      GET:
        1.Get fileName ,fileType of Media from Front-end
        2.Generate presigned urls 
        3.Return presigned url ,url of media 
      POST:
        4.save urls of media (after successful upload from front-end)

    '''
    permission_classes = [IsProductOwner]

    queryset = models.ProductImage.objects.all()
    s3_client=boto3.client("s3",
                           aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME )

    def get(self,request):
        '''
        Generates pre-signed url to upload media to AWS S3

        Access:
            Authenticated
        Response:
             upload url : presigned url to upload from front-end
             ulr        : url of media (after upload)  
        '''

        user=self.request.user

        # file_name for path in s3 , file_type is to seperate videos,images 
        file_name=self.request.GET.get('file_name')
        file_type=self.request.GET.get('file_type')
        product_id=self.request.GET.get('product_id')

        if not all([file_name,file_type,product_id]) :
            return Response({"error":'file_name,file_type and product_id aren required parameters'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product=models.Product.objects.get(id=product_id)
        
            if product.seller.user!=user:  # checking whether the user is actuall seller of the product
                return Response(
                    {"error":"you dont have enough permission to upload media"},
                    status=status.HTTP_403_FORBIDDEN)
        
        except models.Product.DoesNotExist:
            return Response({"error":"product does not exist"},status=status.HTTP_404_NOT_FOUND)
        except Seller.DoesNotExist:
            return Response({"error":"user does not registerd as a seller"},status=status.HTTP_404_NOT_FOUND)

    
        # generate presigned urls for temporary credentials to upload media from front-end
        presigned_urls=self.s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket':settings.AWS_STORAGE_BUCKET_NAME,'Key':f'{user}/{product_id}/{file_type}/{file_name}'},
            ExpiresIn=3600
        )
        # its url that gets generated after successful upload from front-end
        url=f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{user}/{product_id}/{file_type}/{file_name}'
        print(url)
        
        return Response({'upload_url':presigned_urls,'file_url':url,
                         'bucket':settings.AWS_STORAGE_BUCKET_NAME,'key':f'{user}/{product_id}/{file_type}/{file_name}'},
                         status=status.HTTP_200_OK)
    
    def post(self,request):
        '''
        Uploaded url's of media

        Request Body:
        ```json

            {
            "image_url": "URL (String)",
            "alt_text": "String (Optional)",
            "video_url": "URL (Optional/String)",
            "is_primary": "Boolean (true/false)",
            "display_order": "Integer"
            }
        ```
        Response:

            201 created     : url's are saved

            Example:
            ```Json
            {
            "image_url": "https://m.media-amazon.com/images/I/71d7rfSl0WL._SL1500_.jpg",
            "alt_text": "iPhone 15 Pro Titanium Blue - Front View",
            "video_url": "https://www.youtube.com/watch?v=xqyUdNxWn3w",
            "is_primary": true,
            "display_order": 1
              } 
            ```
            400 BAD REQUEST : validation error
        '''

        product_id=self.request.data.get('product_id')
       
        user=self.request.user
       

        if not product_id:
            return Response(
                {"error":"product_id is required in the body"},
                status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product=models.Product.objects.get(id=product_id)
     
            if  product.seller.user!=user:
                return Response(
                    {'error':'you dont have permission to upload media files to this Product'},
                    status=status.HTTP_403_FORBIDDEN)
        except models.Product.DoesNotExist:
            return Response({"error":"Prodcut does not exist"},status=status.HTTP_404_NOT_FOUND)
        except Seller.DoesNotExist:
            return Response({'error':'user does not registerd as a seller'},status=status.HTTP_404_NOT_FOUND)
            

        serializer=serializers.ProductImageSerializers(data=request.data,context={"request":request,"product_id":product_id})
  
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
productImage_retrieve_view=ProductImageListview.as_view()



class ProductCreateGenericView(APIView):

    '''
    Docstring for Product Create API

    Allows Authenticated and Verified Sellers to:

    -Create or List a New Product

    sideEffects:
        - publishes SNS notification after Product creation
    '''
    permission_classes = [IsAuthenticated,IsSeller]


    def post(self,request):
        '''
        Create a New Product
        
        Request Body:
        ```json
        {
            "product_name": "String",
            "description": "String (Optional/Text)",
            "base_price": "Decimal (e.g. 00.00)",
            "category": "String (Category Name)",
            "brand": "String (Brand Name)",
            "sku": "String (Unique)",
            "is_active": "Boolean (true/false)",
            "variants": [
                {
                    "color": "String",
                    "size": "String",
                    "price": "Decimal",
                    "stock_qty": "Integer",
                    "sku": "String (Unique)"
                }
            ]
        }
        
        ```
        Example:
        ```json
        {
            "product_name": "UltraView 4K Monitor",
            "description": "A 27-inch high-performance monitor for creators and gamers.",
            "base_price": "350.00",
            "category": "phones",
            "brand": "apple",
            "sku": "MON-UV4K-001",
            "is_active": true,
            "variants": [
            {
                "color": "Glossy Black",
                "size": "27-inch",
                "price": "350.00",
                "stock_qty": 15,
                "sku": "MON-UV4K-BLK"
                },
            {
                "color": "Matte Silver",
                "size": "27-inch",
                "price": "365.00",
                "stock_qty": 10,
                "sku": "MON-UV4K-SLV"
                }
            ]
        }
        ```
        Workflow:
            1.Validate request data
            2.Save Product
            3.SNS Publish
        
        Responses:
            201: Product created
            Example:
            ```json
            {
            "id": 27,
            "product_name": "UltraView 4K Monitor",
            "category_name": "phones",
            "description": "A 27-inch high-performance monitor for creators and gamers.",
            "base_price": "350.00",
            "category": "phones",
            "brand_name": "apple",
            "brand": "apple",
            "stock_qty": 25,
            "sku": "MON-UV4K-001",
            "is_active": true,
            "variants": [
                {
                    "id": 8,
                    "color": "Glossy Black",
                    "size": "27-inch",
                    "price": "350.00",
                    "stock_qty": 15,
                    "sku": "MON-UV4K-BLK"
                },
                {
                    "id": 9,
                    "color": "Matte Silver",
                    "size": "27-inch",
                    "price": "365.00",
                    "stock_qty": 10,
                    "sku": "MON-UV4K-SLV"
                }
             ]
            }
                       
            ```
            400: Validation Error
            Example:
            ```json
            {
                "category": [
                    "Object with name=Electronics does not exist."
                ],
                "brand": [
                    "Object with name=TechGiant does not exist."
                ],
                "sku": [
                    "product with this sku already exists."
                ]
             }
            
            ```
        '''
        serializer=serializers.ProductCreateSerializers(data=request.data,
                                                        context={'request':request})
        if serializer.is_valid():
            product=serializer.save()

            #notify other systems async
            tasks.notify_product_creator.delay(product.name,self.request.user.username)

            return Response(serializer.data,status=status.HTTP_201_CREATED)     
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
            

product_create_view=ProductCreateGenericView.as_view()
