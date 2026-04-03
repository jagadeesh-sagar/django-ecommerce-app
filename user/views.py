from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser
from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly
from django.db.models import Q
from . import models
from . import serializers
# from django.contrib.auth.models import User
from api.models import User
from inventory.models import Seller
from django.shortcuts import get_object_or_404
import boto3
from django.conf import settings


class ProductsListAPIView(APIView):
    '''
    Products List API

    Allows all users (Aunthenticated or not) to:
       - List all available Products 
        
    '''

    queryset=models.Product.objects.all()

    def get(self,request):
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

        serializer=serializers.ProductSerializer(self.queryset.all(),many=True,context={'request':request})

        return Response(serializer.data,status=status.HTTP_200_OK)


product_view=ProductsListAPIView.as_view()


class ProductCreateGenericView(APIView):

    '''
    Docstring for Product Create API

    Allows Authenticated and Verified Sellers to:

    -Create or List a New Product

    sideEffects:
        - publishes SNS notification after Product creation
    '''
    permission_classes = [IsAuthenticated,IsSeller]

    sns_client=boto3.client("sns",aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_S3_REGION_NAME)
    SNS_TOPIC_ARN=settings.AWS_SNS_ARN
    
    def sns_publish(self,message,user):
        '''
        Publishes a AWS SNS Notification after creation of New Product
 
        :param message: Product name
        :param user: Seller creating Product
        '''
        self.sns_client.publish(TopicArn=self.SNS_TOPIC_ARN,
                                Message=f'$Mr.{user.username} you added {message}',
                                Subject="seller created product",)

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
            self.sns_publish(product.name,self.request.user)

            return Response(serializer.data,status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
            

product_create=ProductCreateGenericView.as_view()


class ProductDetailView(mixins.RetrieveModelMixin,generics.GenericAPIView):
    '''
     Product Detail API
     
     Allows all Users(Authenticated or not) to:
     - List details of a Product

    '''
    permission_classes=[AllowAny]
    queryset=models.Product.objects.all()
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
        return self.retrieve(request,*args,**kwargs)
    
product_detail=ProductDetailView.as_view()


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
     queryset=models.Product.objects.all()

     def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
        
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
        category=self.request.GET.get('ct',None)
        name=self.request.GET.get('n',None)
        brand=self.request.GET.get('b',None)
        price=self.request.GET.get('p',None)
        price_range_variation=1000

        queryset=self.queryset.all()

        if category:
            queryset=queryset.filter(Q(category__name__icontains=category)) 

        if name:
            queryset=queryset.filter(Q(name__icontains=name)) 

        if brand:
            queryset=queryset.filter(Q(brand__name__icontains=brand)) 

        if  price is not None and price.isdigit():
                value=int(price)

                #  Price search includes ±1000 range for price variance (tolerance)
                queryset=queryset.filter(Q(base_price__lte=value+price_range_variation),Q(base_price__gte=value-price_range_variation))
                # queryset = queryset.filter(base_price__range=(min_p, max_p))
        serializer=serializers.ProductSearchSerializers(queryset,many=True,context={'request':request})

        return Response(serializer.data,status=status.HTTP_200_OK)
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
    permission_classes = [IsAuthenticated]

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
        url=f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonsaws.com/{user}/{product_id}/{file_type}/{file_name}'
        
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


class AddressView(generics.GenericAPIView):
    '''
    Address API

    Allows Authenticated users to :
        - add a Address
        - get Address 
        - edit Address

    Methods:
        -GET
        -POST
        -PATCH
    '''
    permission_classes = [IsAuthenticated,IsBuyer]

    serializer_class = serializers.AddressSerializers

    def get_queryset(self):
        return models.Address.objects.filter(user=self.request.user)
    
    def get(self,request):
        '''
        Returns address's of users

        Access:
            Authenticated

        Response:
            -200 ok : Address is returnerd

            Example:
            ```Json
            [
                {
                "user": "jaggu",
                "address_type": "both",
                "house_no": "Plot No. 42, Green Villas",
                "street": "Madhapur Main Road",
                "city": "Hyderabad",
                "state": "Telangana",
                "country": "India",
                "postal_code": 500081,
                "phone_number": "+919876543210",
                "other_number": 1234567890
                }
            ]
            
            ```
        '''
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request):
        '''
        creates a new Address

        Request Body:
        ```Json
            {
                "address_type": "String ('shipping', 'billing', or 'both')",
                "house_no": "String",
                "street": "String",
                "city": "String",
                "state": "String",
                "country": "String",
                "postal_code": "Integer",
                "phone_number": "String",
                "other_number": "Integer (Optional)"
            }
        ```

        Response:
            -201 created: Address created
            Example:
            ```Json
            [
                {
                "user": "jaggu",
                "address_type": "both",
                "house_no": "Plot No. 42, Green Villas",
                "street": "Madhapur Main Road",
                "city": "Hyderabad",
                "state": "Telangana",
                "country": "India",
                "postal_code": 500081,
                "phone_number": "+919876543210",
                "other_number": 1234567890
                }
            ]  
            ```
            -400 Bad request: validation error

        '''
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    
    def patch(self,request):
        '''
        Updating the Address

        request body:
        ```Json
            {
                "address_type": "String ('shipping', 'billing', or 'both')",
                "house_no": "String",
                "street": "String",
                "city": "String",
                "state": "String",
                "country": "String",
                "postal_code": "Integer",
                "phone_number": "String",
                "other_number": "Integer (Optional)"
            }
        ```

        Response:
            -200 ok: Address updated
            -400 Bad request: validation error
        '''
        address=self.get_queryset()
        if not address:
            return Response({"error":"Address not Found"},status=404)
        serializer=self.get_serializer(data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_200_OK)

address_create=AddressView.as_view()


class CategoryListCreateview(generics.ListCreateAPIView):
    '''
    Category API

    Lists and creates all Product categories 

    Access:
        PublicReadOnly
        AdminPrevilages

    Method:
        GET  - returns Product categories
        POST - creates a New Product Category

    request body:
    ```Json
    {
        "name": "String (Unique)",
        "parent": "Integer (Parent Category ID or null)",
        "origin": "String (Optional)",
        "description": "String (Optional)"
    }
    ```
    
    Example:
    ```Json
    {
        "name": "Electronics",
        "parent": null,
        "origin": "Global",
        "description": "Gadgets, appliances, and tech accessories."
    }  
    ```
    '''

    permission_classes=[IsAdminOrReadonly]
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializers
category_view=CategoryListCreateview.as_view()


class SellerAnswers(APIView):
    '''
    SellerQnAAnswers API

    Allows verified and Authenticated Sellers to:
        - Answer to the Customer Questions
    
    Method:
        -GET
        -POST

    '''
   
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
       
        :param kwargs: Description
        '''
        pk=kwargs['pk']
        question=get_object_or_404(self.get_queryset(),id=pk)
        serializer=serializers.SellerAnswersSerializers(question,data=request.data,partial=True,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

seller_ans=SellerAnswers.as_view()


class CustomerQuestion(generics.CreateAPIView):
    '''
    Customer Question API

    Method:
        post-saves the customer question

    Response:
        201 created:customer question posted
    '''
    queryset=models.QnA.objects.all()
    serializer_class=serializers.CustomerQuestionSerializers

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['id'] = self.request.GET.get('q')
        return context
    
customer_qxns=CustomerQuestion.as_view()


class CartItem(APIView):
    '''
    Cart API 
    
    Allows Authenticated users to perfom actions :
        - Add Products to cart
        - Remove products from cart
        - Update the quantity
    '''

    permission_classes=[IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
  
    def get(self,request):
        '''
        Retrives products from users Cart    

        Response :
            200 OK : successfully returns the cart items  
        '''
        # retrives cart if Exists else creates a New one
        cart=models.Cart.objects.get_or_create(user=self.request.user)
        cartitem=models.CartItem.objects.filter(Q(cart__user=cart[0].user))
        serializer=serializers.CartItemRetrieveSerializers(cartitem,many=True,context={'request':request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self,request):
        '''
        Adds Cart item to the cart

        Request body:

        QueryParameters:
           product         : Product ID 
           product_varaint : Product Varaint ID

        Responses:
            200 ok : Cart item is added
            400 Bad request : validation error
      
        '''
        product_id=self.request.get('product')
        variant_id=self.request.get('product_variant')
        quantity=int(self.request.get('quantity',1))

        if not product_id:
            return Response({"error":"product is required"},status=400)
        
        if quantity <=0:
              return Response({"error":"quantity should be positive"},status=400)

        # create a Cart object if does not exits
        cart,_=models.Cart.objects.get_or_create(user=request.user)
        
        try:
            # if cart item already exists update it
            cart_item=models.CartItem.objects.filter(
                cart=cart,
                product_id=product_id,
                product_variant_id=variant_id if variant_id else None
                )
            
            if cart_item:
                cart_item.quantity+=quantity

                if cart_item.product_variant:
                    available_stock=cart_item.product_variant.stock_qty
                else :
                    available_stock=cart_item.product.stock_qty

                if cart_item.quantity>available_stock:
                    return Response(
                        {"error":f'only {available_stock} are available'}
                    )
                cart_item.save()
                serializer=serializers.CartItemCreateSerializers(cart_item)

                return Response(
                {
                    "message": "Cart updated", 
                    "item": serializer.data
                },
                status=status.HTTP_200_OK
            )

        #if cart item does not exists add it 
        except models.CartItem.DoesNotExist:
                
                serializer=serializers.CartItemCreateSerializers(data=request.data,
                                                                 context={'request':request})
                
                if serializer.is_valid():
                    serializer.save()

                return Response(
                {"message": "Item added", "item":serializer.data},
                status=status.HTTP_201_CREATED)
            
        return Response(serializer.error_messages,status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request):
        '''
        Updating the existing cart item (quantity)

        request body:

        QueryParameters:
           product         : Product ID 
           product_varaint : Product Varaint ID

        Responses:
            200 ok : Cart item is updated (updating quantity or remove)
            404 Not Found   : cart item not found
  
        '''

        product_id=self.request.get('product')
        variant_id=self.request.get('product_variant')
        quantity=self.request.get('quantity')

        if not product_id:
            return Response({"error":"product is required"},status=400)
        
        try:
            quantity=int(quantity)
        except(TypeError,ValueError):
            return Response(
                {'error':"invalid quantity"}
            )
         
        cart=models.Cart.objects.get_object_or_404(user=request.user)
      
        try:
            # updates the existing cart item if exists 
            cart_item=models.CartItem.objects.get(
                cart=cart,
                product_id=product_id,
                product_variant_id=variant_id if variant_id else None
                )
            
        except models.CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if quantity<0:
            cart_item.delete()
            return Response({"message": "Item removed from cart"},
                status=status.HTTP_200_OK
            )
        

        if cart_item.product_variant:
            available_stock=cart_item.product_variant.stock_qty
        else :
            available_stock=cart_item.product.stock_qty

        if cart_item.quantity>available_stock:
            return Response(
                {"error":f'only {available_stock} are available'}
            )
        
        #updates the cart item quantity
        cart_item.quantity = quantity
        cart_item.save()
        serializer=serializers.CartItemCreateSerializers(cart_item)

        return Response(
        {
            "message": "Cart updated", 
            "item": serializer.data
        },
        status=status.HTTP_200_OK
    )
    
    def delete(self, request):
        '''
        QueryParameters:
           product         : Product ID 
           product_varaint : Product Varaint ID

        Responses:
            200 ok        : Cart item is deleted 
            404 Not Found : cart item not found
        '''
     
        product_id = request.query_params.get('product')
        variant_id = request.query_params.get('variant')

        if not product_id:
            return Response(
                {"error": "Product ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        cart = get_object_or_404(models.Cart, user=request.user)
        
        try:
            # if cartitem exists delete it 
            cart_item = models.CartItem.objects.get(
                cart=cart,
                product_id=product_id,
                product_variant_id=variant_id if variant_id and variant_id != "0" else None
            )
            cart_item.delete()
            
            return Response(
                {"message": "Item removed from cart"},
                status=status.HTTP_200_OK
            )
            
        except models.CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, 
                status=status.HTTP_404_NOT_FOUND
            )

              
cartitem=CartItem.as_view()


class ReviewView(APIView):
    '''
    Review API

    Allows Authenticated and verified Customers of products to :
        - ADD Review through media and text
        - Edit the Review
        - Delete the Review   
    '''

    permission_classes=[IsAuthenticated]

    queryset=models.Review.objects.all()

    def post(self,request):
        '''
        Add the Verified Customer Review
        
        Request body:

        QueryParameters :
            q : Product ID

        Responses:
            -200 OK          : Review is added
            -400 BAD REQUEST : Validation error
        
        '''

        product_id = request.GET.get('q')  
        if not product_id:
            return Response(
                {"error": "Product id (q) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer=serializers.ReviewSerializers(data=request.data,context={'id': product_id,'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request):
        '''
        Edits existing review for customer

        request body:

        Responses:
            - 200 OK : Review Updated
            - 400 BAD REQUEST : Validation error
            - 404 NOT FOUND   : Review Not Found
        '''

        product_id = request.GET.get('q')  
        if not product_id:
            return Response(
                {"error": "Product id (q) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        review=models.Review.objects.filter(
            user=request.user,
            product_id=product_id
        ).first()

        if not review:
            return Response(
               { "error":"review does not exist"},
               status=status.HTTP_404_NOT_FOUND
            )
        else:
            serializer=serializers.ReviewSerializers(review,
                                                     data=request.data,
                                                     partial=True,
                                                     context={'id': product_id,'request':request})
            if serializer.is_valid():
               serializer.save()
               return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST) 
    
    def delete(self,request):
        '''
        QueryParameters:
            q : Product ID

        Responses:
            200 ok        : Review item is deleted 
            404 Not Found : Review item not found
        '''
        product_id = request.GET.get('q')  
        if not product_id:
            return Response(
                {"error": "Product id (q) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        count_review,_=models.Review.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()

        if count_review==0:
            return Response({"error":"review is not found"},
                            status=status.HTTP_404_NOT_FOUND)
     
        return Response({"message":"deleted successfully"},status=status.HTTP_200_OK)
    
review_list_view=ReviewView.as_view()


class BrandListCreateview(generics.ListCreateAPIView):
    '''
    Brand API

    Allows verified and Authenticated Sellers to do Actions:
        - create new Brands
    Methods:
        POST
        GET
 
    '''
    queryset=models.Brand.objects.all()
    serializer_class=serializers.BrandSerializer

brand_list_create_view=BrandListCreateview.as_view()


class WhishView(APIView):
    '''
    Allows Authenticated customers to:
        - ADD Products to the wishlist
        - Delete(Remove) from Wishlist
        - Get Products from Whishlist
    '''
    queryset=models.Whishlist.objects.all()
    permission_classes=[IsAuthenticated]

    def get(self,request):
        '''
        Returns the products from Whishlist:

        Access:
            Authenticated
        Response:
            200 ok -Products from Whishlist
        '''
        queryset = self.queryset.filter(user=request.user)
        serializer=serializers.WhishlistReadSerializer(queryset,many=True,
                                                   context={"request":request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self,request):
        '''
        Add Products to the Wishlist

        Request Body:
            -Product id

        Responses:
            201:Product added
            400:Validation Error
  
        '''
        product_id = request.GET.get('q')  
        if not product_id:
            return Response(
                {"error": "Product id (q) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer=serializers.WhishlistCreateSerializer(data=request.data,
                                                   context={"request":request,"id":product_id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request):
        '''
        Removes Product from Wishlist:

        Request Body:
            -Product id
        Responses:
            200 : Deleted
            404 : Product not found

        '''
        product_id = request.GET.get('q')  
        if not product_id:
            return Response(
                {"error": "Product id (q) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count,_=self.queryset.filter(user=self.request.user,product_id=product_id).delete()

        if deleted_count==0:
            return Response({"error":"item is not found"},
                            status=status.HTTP_404_NOT_FOUND)
    
        return Response({"message":"deleted successfully"},status=status.HTTP_200_OK)

whish_list_createview = WhishView.as_view()


class OrderView(APIView):

    '''
    Allows Authenticated customers to:
        - Order Products 
        - View Orders
    '''

    def post(self,request):
         '''
         Add Products to Order

         Request Body:

         Responses:
            201:Product added
            400:validation Error
         '''
         serializer=serializers.OrderSerializer(data=request.data,context={'request':request})
         if serializer.is_valid():
             serializer.save()
             return Response(serializer.data,status=status.HTTP_201_CREATED)
         return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def get(self,request):
        '''
        Returns Orders :

        Access:
            Authenticated
        Response:
            200 ok - Orders
        '''
        queryset=models.Order.objects.filter(user=self.request.user)
        serializer=serializers.OrderReadSerializers(queryset,many=True,context={"request":request})
        return Response(serializer.data,status=status.HTTP_200_OK)

order_list_create_view=OrderView.as_view()


class PaymentVIew(generics.ListCreateAPIView):
    queryset=models.Payment.objects.all()
    serializer_class=serializers.PaymentSerializers

payment_list_create_view=PaymentVIew.as_view()

    

