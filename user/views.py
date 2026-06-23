from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser
from rest_framework.pagination import LimitOffsetPagination,CursorPagination,PageNumberPagination

from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly,IsDeliveredProductBuyer
from api.pagination import StandardPagination,LimitOffsetPagination,ProductCursorPagination
from api.authentication import CookieJWTAuthentication
from . import models
from . import serializers

import anthropic
import boto3
from django.conf import settings


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
             - supports ?search=<query> for name filtering
        POST - creates a New Product Category
    '''

    permission_classes=[IsAdminOrReadonly]
    serializer_class = serializers.CategorySerializers

    def get_queryset(self):
        qs = models.Category.objects.all().order_by('name')
        q = self.request.query_params.get('search', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

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

    permission_classes=[IsBuyer, IsDeliveredProductBuyer]

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
    
        review = models.Review.objects.filter(
            user=request.user,
            product_id=product_id
        ).first()

        if not review:
            return Response({"error":"review is not found"},
                            status=status.HTTP_404_NOT_FOUND)
                            
        # Gather all S3 keys from ReviewMedia before deleting
        from urllib.parse import urlparse
        media_urls = list(review.media.values_list('url', flat=True))
        s3_keys = []
        for url in media_urls:
            try:
                parsed = urlparse(url)
                # The path typically starts with a '/', so strip it
                key = parsed.path.lstrip('/')
                s3_keys.append(key)
            except Exception:
                pass
                
        # Trigger Celery task if there are media files
        if s3_keys:
            from .tasks import delete_s3_files
            delete_s3_files.delay(s3_keys)
            
        review.delete()
     
        return Response({"message":"deleted successfully"},status=status.HTTP_200_OK)
    
review_list_view=ReviewView.as_view()


class ReviewMediaPresignView(APIView):
    '''
    Review Media Upload API

    Allows authenticated buyers to attach images/videos to their reviews
    via S3 pre-signed URLs (same pattern as product image uploads).

    Constraints (enforced on POST):
        - max 5 images per review
        - max 1 video  per review

    Flow:
        1. GET  ?file_name=&file_type=images|videos&review_id=
           → { upload_url, file_url }   (pre-signed PUT to S3)
        2. PUT  <upload_url>  (done entirely from the browser — no Django involved)
        3. POST { review_id, url, media_type, display_order }
           → saves ReviewMedia row
    '''
    permission_classes = [IsAuthenticated]

    _s3 = None

    def _get_s3(self):
        if self._s3 is None:
            ReviewMediaPresignView._s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )
        return self._s3

    def get(self, request):
        '''Generate a pre-signed S3 PUT URL for a review media file.'''
        file_name  = request.GET.get('file_name')
        file_type  = request.GET.get('file_type', 'images')   # 'images' or 'videos'
        review_id  = request.GET.get('review_id')

        if not all([file_name, review_id]):
            return Response(
                {'error': 'file_name and review_id are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            review = models.Review.objects.get(id=review_id)
        except models.Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only the review owner may upload media for it
        if review.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        user = request.user
        s3_key = f'{user}/reviews/{review_id}/{file_type}/{file_name}'

        presigned_url = self._get_s3().generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key,
            },
            ExpiresIn=3600,
        )
        file_url = (
            f'https://{settings.AWS_STORAGE_BUCKET_NAME}'
            f'.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}'
        )
        return Response({'upload_url': presigned_url, 'file_url': file_url})

    def post(self, request):
        '''Save a ReviewMedia row after the browser PUT to S3 succeeds.'''
        review_id   = request.data.get('review_id')
        url         = request.data.get('url')
        media_type  = request.data.get('media_type', 'image')
        display_order = request.data.get('display_order', 1)

        if not all([review_id, url]):
            return Response(
                {'error': 'review_id and url are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            review = models.Review.objects.get(id=review_id)
        except models.Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

        if review.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = serializers.ReviewMediaSerializer(
            data={'url': url, 'media_type': media_type, 'display_order': display_order},
            context={'review': review},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        '''Delete a ReviewMedia item and its corresponding S3 file.'''
        media_id = request.GET.get('id')
        if not media_id:
            return Response(
                {"error": "Media id (id) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            media = models.ReviewMedia.objects.get(id=media_id)
        except models.ReviewMedia.DoesNotExist:
            return Response({"error": "Media not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if media.review.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            
        # Trigger Celery task to delete from S3
        from urllib.parse import urlparse
        try:
            parsed = urlparse(media.url)
            s3_key = parsed.path.lstrip('/')
            from .tasks import delete_s3_files
            delete_s3_files.delay([s3_key])
        except Exception:
            pass
            
        media.delete()
        return Response({"message": "Media deleted successfully"}, status=status.HTTP_200_OK)


review_media_view = ReviewMediaPresignView.as_view()


class BrandListCreateview(generics.ListCreateAPIView):
    '''
    Brand API

    Allows verified and Authenticated Sellers to:
        - List all Brands
        - Search brands by name: GET /user/brand/?search=<query>
        - Create a new Brand

    Methods:
        GET  - Returns all Brands (no pagination — full list for dropdowns)
             - supports ?search=<name> for live search
        POST - Creates a new Brand

    Access:
        Authenticated Sellers only
    '''
    permission_classes=[IsSeller]
    serializer_class=serializers.BrandSerializer

    def get_queryset(self):
        qs = models.Brand.objects.all().order_by('name')
        q = self.request.query_params.get('search', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

brand_list_create_view=BrandListCreateview.as_view()

    
class AnthropicProxyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "prompt is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prefer the cookie; fall back to the Authorization header value
        jwt_token = request.COOKIES.get("access", "")
        if not jwt_token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                jwt_token = auth_header.split(" ", 1)[1]

        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            message = client.beta.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                betas=["mcp-client-2025-04-04"],
                system=(
                    "You are a helpful e-commerce assistant. "
                    "Use the available tools to fulfil the user's request "
                    "and respond in plain language."
                ),
                messages=[{"role": "user", "content": prompt}],
                mcp_servers=[
                    {
                        "type": "url",
                        "url": settings.MCP_SERVER_URL,
                        "name": "ecommerce-mcp",
                        "tool_configuration": {"enabled": True},
                        "authorization_token": jwt_token,
                    }
                ],
            )

            # content is a mixed list: TextBlock, ToolUseBlock, ToolResultBlock …
            # Pick the last TextBlock — that's Claude's final answer after tool calls.
            text_blocks = [
                block for block in message.content
                if getattr(block, "type", None) == "text"
            ]
            response_text = (
                text_blocks[-1].text
                if text_blocks
                else "I couldn't generate a response. Please try again."
            )

            return Response(
                {"response": response_text},
                status=status.HTTP_200_OK
            )

        except anthropic.APIError as e:
            return Response(
                {"error": f"Anthropic API error: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


anthropic_proxy_view = AnthropicProxyView.as_view()