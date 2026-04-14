from rest_framework.views import APIView
from rest_framework import generics,mixins,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser

from .permissions import IsBuyer,IsSeller,IsSellerOrReadOnly,IsProductOwner,IsAdminOrReadonly
from django.db.models import Q
from . import models
from . import serializers
from api.pagination import StandardPagination,LimitOffsetPagination,ProductCursorPagination

from django.shortcuts import get_object_or_404

from api.authentication import CookieJWTAuthentication

class CartItem(APIView):
    '''
    Cart API 
    
    Allows Authenticated users to perfom actions :
        - Add Products to cart
        - Remove products from cart
        - Update the quantity
    '''

    permission_classes=[IsBuyer]
  
    def get(self,request):
        '''
        Retrives products from users Cart    

        Response :
            200 OK : successfully returns the cart items  
            ```json
        [
            {
                "cart": 3,
                "product": {
                    "id": 1,
                    "product_name": "samsung s23",
                    "category_name": "phones",
                    "brand_name": "samsung",
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
                            "review_text": "good phone",
                            "review_image": "",
                            "review_video": "",
                            "is_verified_purchase": true
                        }
                    ]
                },
                "product_variant": null,
                "quantity": 2,
                "cartitem": "http://127.0.0.1:8000/user/cart/?product=1&variant=None"
            }
        ]
            ```
        '''
        # retrives cart if Exists else creates a New one
        cart=models.Cart.objects.get_or_create(user=self.request.user)
        cartitem=models.CartItem.objects.filter(Q(cart__user=cart[0].user))

        paginator=StandardPagination()
        result_page=paginator.paginate_queryset(cartitem,request)

        serializer=serializers.CartItemRetrieveSerializers(result_page,many=True,context={'request':request})
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self,request):
        '''
        Adds Cart item to the cart

        Request body:
        ```json
        {
            "product": "Integer (Product ID)",
            "product_varaint": "Integer (Variant ID - Optional)",
            "quantity": "Integer"
        }
        ```

        Responses:
            200 ok : Cart item is added

            400 Bad request : validation error
      
        '''
        product_id=self.request.data.get('product')
        variant_id=self.request.data.get('product_variant')
        quantity=int(self.request.data.get('quantity',1))

        if not product_id:
            return Response({"error":"product is required"},status=400)
        
        if quantity <=0:
              return Response({"error":"quantity should be positive"},status=400)

        # create a Cart object if does not exits
        cart,_=models.Cart.objects.get_or_create(user=request.user)
        
        try:
            # if cart item already exists update it
            cart_item=models.CartItem.objects.get(
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
                        ,status=status.HTTP_400_BAD_REQUEST
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

        Request Body:
        ```json
        {
            "product": "Integer (Product ID)",
            "product_variant": "Integer (Variant ID - Optional/null)",
            "quantity": "Integer (use negative value to remove item)"
        }
        ```

        Example:
        ```json
        {
            "product": 1,
            "product_variant": 12,
            "quantity": 3
        }
        ```

        Note:
            - Pass a negative quantity (e.g. -1) to remove the item from the cart entirely
            - quantity must be a valid integer

        QueryParameters:
           product         : Product ID
           product_varaint : Product Varaint ID

        Responses:
            200 ok : Cart item is updated (updating quantity or remove)
            Example (quantity updated):
            ```json
            {
                "message": "Cart updated",
                "item": {
                    "product": 1,
                    "product_variant": 12,
                    "quantity": 3
                }
            }
            ```
            Example (item removed, quantity < 0):
            ```json
            {
                "message": "Item removed from cart"
            }
            ```
            404 Not Found   : cart item not found
            ```json
            {
                "error": "Item not found in cart"
            }
            ```

        '''

        product_id=self.request.data.get('product')
        variant_id=self.request.data.get('product_variant')
        quantity=int(self.request.data.get('quantity',1))

        if not product_id:
            return Response({"error":"product is required"},status=400)
        
        try:
            quantity=int(quantity)
        except(TypeError,ValueError):
            return Response(
                {'error':"invalid quantity"}
            )
         
        cart=get_object_or_404(models.Cart,user=request.user)
      
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

              
cartitem_view=CartItem.as_view()



class WhishView(APIView):
    '''
    Allows Authenticated customers to:
        - ADD Products to the wishlist
        - Delete(Remove) from Wishlist
        - Get Products from Whishlist
    '''

    permission_classes=[IsBuyer]

    def get(self,request):
        '''
        Returns the products from the authenticated user's Wishlist

        Access:
            Authenticated

        Response:
            200 OK - Products from Wishlist
            Example:
            ```json
            [
                {
                    "product": {
                        "product_name": "samsung s23",
                        "description": "good phone",
                        "category_name": "phones",
                        "base_price": "20000.00",
                        "brand_name": "samsung",
                        "product_detail": "http://127.0.0.1:8000/user/product/detail/1"
                    }
                }
            ]
            ```
        '''
        queryset = models.Whishlist.objects.filter(user=request.user)

        if not queryset.exists():
            return Response({"message":"Whishlist is  empty"},status=status.HTTP_200_OK)

        paginator=StandardPagination()
        result_page=paginator.paginate_queryset(queryset,request)

        serializer=serializers.WhishlistReadSerializer(result_page,many=True,
                                                   context={"request":request})
        return paginator.get_paginated_response(serializer.data)
    
    def post(self,request):
        '''
        Add a Product to the authenticated user's Wishlist

        QueryParameters:
            q : Product ID (required)

        Example:
            POST /user/whishlist/?q=1

        Responses:
            201 CREATED : Product added to Wishlist
            Example:
            ```json
            {}
            ```
            400 BAD REQUEST : Validation error
            Example:
            ```json
            {
                "non_field_errors": [
                    "This product is already in your wishlist."
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

        serializer=serializers.WhishlistCreateSerializer(data=request.data,
                                                   context={"request":request,"id":product_id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request):
        '''
        Removes a Product from the authenticated user's Wishlist

        QueryParameters:
            q : Product ID (required)

        Example:
            DELETE /user/whishlist/?q=1

        Responses:
            200 OK : Product removed from Wishlist
            Example:
            ```json
            {
                "message": "deleted successfully"
            }
            ```
            404 NOT FOUND : Product not in Wishlist
            Example:
            ```json
            {
                "error": "item is not found"
            }
            ```

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

wishlist_view = WhishView.as_view()







