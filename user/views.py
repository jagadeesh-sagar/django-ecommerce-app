from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser
from rest_framework.pagination import LimitOffsetPagination,CursorPagination,PageNumberPagination

from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly
from api.pagination import StandardPagination,LimitOffsetPagination,ProductCursorPagination
from api.authentication import CookieJWTAuthentication
from . import models
from . import serializers



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
    permission_classes = [IsAuthenticated]

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
        address_id=self.request.GET.get('q')
        address=self.get_queryset().filter(id=address_id).first()

        print(address,address_id)
    
        if not address:
            return Response({"error":"Address not Found"},status=404)
        serializer=self.get_serializer(address,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_200_OK)

address_create_view=AddressView.as_view()


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


class CustomerQuestion(generics.CreateAPIView):
    '''
    Customer Question API

    Method:
        post-saves the customer question
    Request-Body:
    ```json
        {
        "question": "String (The text of the customer's question)"
        }
    ```

    Response:
        201 created:customer question posted
        Example:
        ```Json
        {
        "id": "25",
        "question": "Does this monitor support HDMI 2.1 for 120Hz gaming?",
        "endpoint": "http://127.0.0.1:8000/api/user/product/qna/"
        }  
        ```
    '''
    queryset=models.QnA.objects.all()
    serializer_class=serializers.CustomerQuestionSerializers
    permission_classes=[IsBuyer]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['id'] = self.request.GET.get('q')
        return context
    
customer_qxns_view=CustomerQuestion.as_view()

class ReviewView(APIView):
    '''
    Review API

    Allows Authenticated and verified Customers of products to :
        - ADD Review through media and text
        - Edit the Review
        - Delete the Review   
    '''

    permission_classes=[IsBuyer]

    queryset=models.Review.objects.all()

    def post(self,request):
        '''
        Add the Verified Customer Review

        Request Body:
        ```json
        {
            "rating": "Integer (1 to 5)",
            "review_text": "String (Optional)",
            "review_image": "URL (Optional)",
            "review_video": "URL (Optional)",
            "is_verified_purchase": "Boolean (true/false)"
        }
        ```

        Example:
        ```json
        {
            "rating": 4,
            "review_text": "Good phone, fast delivery.",
            "review_image": "https://example.com/review-image.jpg",
            "review_video": "",
            "is_verified_purchase": true
        }
        ```

        QueryParameters :
            q : Product ID

        Responses:
            201 CREATED : Review is added
            Example:
            ```json
            {
                "rating": 4,
                "review_text": "Good phone, fast delivery.",
                "review_image": "https://example.com/review-image.jpg",
                "review_video": "",
                "is_verified_purchase": true
            }
            ```
            400 BAD REQUEST : Validation error
            Example:
            ```json
            {
                "non_field_errors": [
                    "you have already reviewed this product"
                ]
            }
            ```

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
        Edits existing review for the authenticated customer

        Request Body (all fields optional — partial update):
        ```json
        {
            "rating": "Integer (1 to 5)",
            "review_text": "String (Optional)",
            "review_image": "URL (Optional)",
            "review_video": "URL (Optional)",
            "is_verified_purchase": "Boolean (true/false)"
        }
        ```

        Example:
        ```json
        {
            "rating": 5,
            "review_text": "Updated: even better after a week of use!"
        }
        ```

        QueryParameters :
            q : Product ID

        Responses:
            200 OK : Review Updated
            Example:
            ```json
            {
                "rating": 5,
                "review_text": "Updated: even better after a week of use!",
                "review_image": "https://example.com/review-image.jpg",
                "review_video": "",
                "is_verified_purchase": true
            }
            ```
            400 BAD REQUEST : Validation error
            404 NOT FOUND   : Review Not Found
            ```json
            {
                "error": "review does not exist"
            }
            ```
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
               return Response(serializer.data,status=status.HTTP_200_OK)
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

    Allows verified and Authenticated Sellers to:
        - List all Brands
        - Create a new Brand

    Methods:
        GET  - Returns all Brands
        POST - Creates a new Brand

    Access:
        Authenticated Sellers only

    GET Response:
        200 OK - List of Brands
        Example:
        ```json
        [
            {
                "id": 1,
                "name": "samsung",
                "logo": "https://example.com/samsung-logo.png",
                "description": "South Korean multinational electronics company.",
                "is_active": true
            },
            {
                "id": 2,
                "name": "apple",
                "logo": "https://example.com/apple-logo.png",
                "description": "American multinational technology company.",
                "is_active": true
            }
        ]
        ```

    POST Request Body:
        ```json
        {
            "name": "String (Unique)",
            "logo": "URL (Optional)",
            "description": "String (Optional)",
            "is_active": "Boolean (true/false)"
        }
        ```

        Example:
        ```json
        {
            "name": "OnePlus",
            "logo": "https://example.com/oneplus-logo.png",
            "description": "Chinese smartphone manufacturer.",
            "is_active": true
        }
        ```

    POST Response:
        201 CREATED - Brand created
        Example:
        ```json
        {
            "id": 3,
            "name": "OnePlus",
            "logo": "https://example.com/oneplus-logo.png",
            "description": "Chinese smartphone manufacturer.",
            "is_active": true
        }
        ```
        400 BAD REQUEST - Validation error
        Example:
        ```json
        {
            "name": [
                "brand with this name already exists."
            ]
        }
        ```
    '''
    permission_classes=[IsSeller]
    queryset=models.Brand.objects.all()
    serializer_class=serializers.BrandSerializer

brand_list_create_view=BrandListCreateview.as_view()

    
