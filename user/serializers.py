# from django.contrib.auth.models import User
from api.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.response import Response
from . import models 
from inventory.models import Seller 
from django.db.models import Q
from django.utils import timezone
from rest_framework.reverse import reverse
from django.db import transaction
from decimal import Decimal 


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model=models.Category
        fields=['name','parent','origin','description']


class ProductImageSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImage
        fields = ['image_url', 'alt_text', 'video_url', 
                  'is_primary', 'display_order']

    def create(self,validated_data):
            product_id=self.context.get('product_id')
            print(product_id,'j')

            if not product_id :
                raise serializers.ValidationError({"error":"product Id is required to create ProductImage"})
            
            try:
                product=models.Product.objects.get(id=product_id)
            except models.Product.DoesNotExist:
                raise serializers.ValidationError({"error":"Product does not exist with this id"})
           
            validated_data['product']=product

            return super().create(validated_data)
        

class ReviewSerializers(serializers.ModelSerializer):

    class Meta:
        model = models.Review
        fields = [
            'rating',
            'review_text',
            'review_image',
            'review_video',
            'is_verified_purchase',
        ]

    def validate(self,attrs):
        user=self.context["request"].user
        product_id=self.context.get('id')

        if self.instance is not None:
            return attrs
        
        if models.Review.objects.filter(user=user,product_id=product_id).exists():
            raise serializers.ValidationError(
                'you have already reviewed this product ')
        
        return attrs
    
    def create(self,validated_data):
        product=self.context.get('id')
        validated_data['product_id']=product
        validated_data['user']=self.context['request'].user
        return super().create(validated_data)


class ProductVariantSerializers(serializers.ModelSerializer):
 
    class Meta:
        model=models.ProductVariant
        fields=['id','color','size','price','stock_qty','sku']

    def get_product_name(self,obj):
       return obj.product.name
        

class CustomerQuestionSerializers(serializers.ModelSerializer):
  
    endpoint=serializers.SerializerMethodField()
    id=serializers.CharField(read_only=True)
  
    class Meta:
        model=models.QnA
        fields=["id",'question','endpoint']
    
    def get_endpoint(self,obj):
        request=self.context.get('request')
        if request is None:
            return None
      
        url=reverse('qna',request=request)
        return url

    def create(self, validated_data):
        product=self.context.get('id')
        validated_data['product_id']=product
        validated_data['user']=self.context['request'].user
        return super().create(validated_data)
    

class QnA(serializers.ModelSerializer):

    endpoint=serializers.SerializerMethodField()
    product=serializers.CharField(write_only=True)
    id=serializers.CharField(write_only=True)

    class Meta:
        model=models.QnA
        fields=['id','question','answer','product','endpoint']

    def get_endpoint(self,obj):
        request=self.context.get('request')
        if request is None:
            return None
        url=reverse('qna-ans',kwargs={"pk":obj.id},request=request)
        return url

    def create(self, validated_data):
        validated_data['user']=self.context['request'].user
        return super().create(validated_data)
    

class ProductSearchSerializers(serializers.ModelSerializer):

    product_name=serializers.CharField(source="name")
    category_name=serializers.CharField(source='category.name',read_only=True)
    category=serializers.PrimaryKeyRelatedField(queryset=models.Category.objects.all(),write_only=True)
    brand_name=  serializers.CharField(source='brand.name',read_only=True)
    brand=serializers.PrimaryKeyRelatedField(queryset=models.Brand.objects.all(),write_only=True)
    seller_name=serializers.SerializerMethodField(read_only=True)
    variants=ProductVariantSerializers(many=True,read_only=True)
    seller=serializers.PrimaryKeyRelatedField(queryset=Seller.objects.all(),write_only=True)

    class Meta:
        model=models.Product
        fields=['seller','seller_name','product_name','category_name',
                'base_price','category','brand_name','variants','brand']

    def get_seller_name(self, obj):
       return obj.seller.user.username
    

class ProductDetailSerializers(serializers.ModelSerializer):

    product_name=serializers.CharField(source="name")
    category_name=serializers.CharField(source='category.name',read_only=True)
    category=serializers.PrimaryKeyRelatedField(queryset=models.Category.objects.all(),write_only=True)
    brand_name=  serializers.CharField(source='brand.name',read_only=True)
    brand=serializers.PrimaryKeyRelatedField(queryset=models.Brand.objects.all(),write_only=True)
    seller_name=serializers.SerializerMethodField(read_only=True)
    images=ProductImageSerializers(many=True,read_only=True)
    variants=ProductVariantSerializers(many=True,read_only=True)
    reviews=ReviewSerializers(many=True,read_only=True)
    new_review=serializers.SerializerMethodField()
    seller=serializers.PrimaryKeyRelatedField(queryset=Seller.objects.all(),write_only=True)
    new_question=serializers.SerializerMethodField()
    questions=QnA(many=True)
    whishlist=serializers.SerializerMethodField()

    class Meta:
        model=models.Product
        fields=['seller','seller_name','images','product_name','category_name'
                ,'description','base_price','category','brand_name',
            'brand','stock_qty','sku','is_active','images','variants','reviews','new_review','questions','new_question','whishlist'
            ]

    def get_seller_name(self, obj):
       return obj.seller.user.username
    
    def get_new_question(self,obj):
        request=self.context.get('request')
        if request is None:
            return None
        url=reverse('qna',request=request)
        return f'{url}?q={obj.id}'
    
    def get_new_review(self,obj):
        request=self.context.get('request')
        if request is None:
            return None
        url=reverse(f'product-review',request=request)
        return f'{url}?q={obj.id}'
    
    def get_whishlist(self,obj):
        request=self.context.get('request')
        if request is None:
            return None
        url=reverse(f'whishlist',request=request)
        return f'{url}?q={obj.id}'


class ProductCreateSerializers(serializers.ModelSerializer):

    product_name=serializers.CharField(source="name")
    category_name=serializers.CharField(source='category.name',read_only=True)
    brand_name=  serializers.CharField(source='brand.name',read_only=True)
    # images=ProductImageSerializers(many=True)
    variants=ProductVariantSerializers(many=True,required=False)

    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=models.Category.objects.all()
    )
    brand = serializers.SlugRelatedField(
        slug_field='name',
        queryset=models.Brand.objects.all()
    )

    class Meta:
        model=models.Product
        fields=['id','product_name','category_name','description','base_price',
                'category','brand_name','brand','stock_qty','sku','is_active','variants']
        
        read_only_fields=['id']

    def create(self, validated_data):
        # image_data=validated_data.pop('images',[])
        variant_data=validated_data.pop('variants',[])

        if variant_data:
            variant_stock=sum(v.get('stock_qty') for v in variant_data)
            validated_data['stock_qty']=variant_stock

        elif "stock_qty" not in validated_data:
            validated_data['stock_qty']=0

        user = self.context['request'].user
        seller=Seller.objects.get(user=user)
        validated_data['seller'] = seller

        product=models.Product.objects.create(**validated_data)

        # for image in image_data:
        #     models.ProductImage.objects.create(product=product,**image)
        
        for variant in variant_data:
            models.ProductVariant.objects.create(product=product,**variant)

        return product
        
    
class ProductSerializer(serializers.ModelSerializer):

    product_name=serializers.CharField(source="name")
    category_name=serializers.CharField(source='category.name',read_only=True)
    category=serializers.PrimaryKeyRelatedField(queryset=models.Category.objects.all(),write_only=True)
    brand_name=  serializers.CharField(source='brand.name',read_only=True)
    brand=serializers.PrimaryKeyRelatedField(queryset=models.Brand.objects.all(),write_only=True)    
    product_detail=serializers.SerializerMethodField()


    class Meta:
        model=models.Product
        fields=['product_name','description','category_name','base_price',
                'category','brand_name','brand','product_detail']
        
    def get_product_detail(self,obj):
        request=self.context.get('request')
        if request is None:
            return None
        url=reverse(f'product-detail',kwargs={"pk":obj.id},request=request)
        return f'{url}'


class AddressSerializers(serializers.ModelSerializer):
    user=serializers.CharField(read_only=True)
    
    class Meta:
        model=models.Address
        fields=['user','address_type','house_no','street','city','state','country',
                'postal_code','phone_number','other_number']

    def create(self, validated_data):
        validated_data['user']=self.context['request'].user
        return super().create(validated_data)
    

class SellerAnswersSerializers(serializers.ModelSerializer):
    
    question=serializers.CharField(read_only=True)
    class Meta:
        model=models.QnA
        fields=['id','answer','product','question']     

    def update(self,instance, validated_data):
        answered_by=self.context['request'].user
        instance.answered_by=answered_by
        if validated_data['answer']:
            instance.is_answered=True
        instance.answered_at=timezone.now()
   
        return super().update(instance,validated_data)


class ProductCartSerializers(serializers.ModelSerializer):

    product_name=serializers.CharField(source="name")
    category_name=serializers.CharField(source='category.name',read_only=True)
    brand_name=  serializers.CharField(source='brand.name',read_only=True)
    seller_name=serializers.SerializerMethodField(read_only=True)
    images=ProductImageSerializers(many=True,read_only=True)
    variants=ProductVariantSerializers(many=True,read_only=True)
    reviews=ReviewSerializers(many=True,read_only=True)
  

    class Meta:
        model=models.Product
        fields=['id','product_name','category_name','brand_name','seller_name',
                'images','variants','reviews']

    def get_seller_name(self, obj):
       return obj.seller.user.username
    

class CartItemRetrieveSerializers(serializers.ModelSerializer):

    product=ProductCartSerializers(read_only=True)
    class Meta:
        model=models.CartItem
        fields=['cart','product','product_variant','quantity']


class CartItemCreateSerializers(serializers.ModelSerializer):

    product=serializers.PrimaryKeyRelatedField(
        queryset=models.Product.objects.all()
    )

    product_varaint=serializers.PrimaryKeyRelatedField(
        queryset=models.ProductVariant.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = models.CartItem
        fields = ['product','product_varaint','quantity']

    def validate(self, attrs):
        
        prodcut=attrs.get('product')
        variant=attrs.get('product_varaint')

        if variant and variant.Product != prodcut:
            raise serializers.ValidationError(
                "Selected variant does not belong to this product")
        
        if variant:
            if variant.stock_qty>attrs['quantity']:
                raise serializers.ValidationError(
                f"Only {variant.stock_qty} items available"
                )
            else :
                if prodcut.stock_qty > attrs['quantity']:
                    raise serializers.ValidationError(
                    f"Only {prodcut.stock_qty} items available"
                    )

        return super().validate(attrs)

    def create(self, validated_data):
    
        user = self.context['request'].user
        cart, created = models.Cart.objects.get_or_create(user=user)
        validated_data['cart'] = cart
        return super().create(validated_data)
    

class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model =models.Brand
        fields = '__all__'


class WhishlistCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.Whishlist
        fields=[]

    def validate(self,attrs):
        user=self.context['request'].user
        product_id=self.context['id']
        if models.Whishlist.objects.filter(user=user,
                                           product_id=product_id).exists(): # filter does not returns None its returns []
            raise serializers.ValidationError(
               "This product is already in your wishlist."
            )
        return attrs
    
    def create(self,validated_data):

        product_id=self.context['id']
        validated_data["product_id"]=product_id
        validated_data['user']=self.context['request'].user
        return super().create(validated_data)

class WhishlistReadSerializer(serializers.ModelSerializer):

    product=ProductSerializer(read_only=True)
    
    class Meta:
        model=models.Whishlist
        fields=['product']

class OrderItemSerializer(serializers.ModelSerializer):

    product_name=serializers.CharField(source="product.name",read_only=True)
    class Meta:
        model=models.OrderItem
        fields=["product","product_name","product_variant","quantity"]

class OrderSerializer(serializers.ModelSerializer):

    items=OrderItemSerializer(required=True,many=True)
    
    class Meta:
        model=models.Order
        fields=['shipping_address','billing_address','coupon','items']
        read_only_fields = ['order_number', 'subtotal', 'total_amount']

    @transaction.atomic
    def create(self,validated_data):
            order_item=validated_data.pop('items')
            import uuid
            order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
            validated_data['order_number']=order_number

            subtotal=0
            if order_item:
                product=order_item['product']
                variant=order_item.get('product_variant')
                quantity=order_item['quantity']
                total_price=0

                unit_price=variant.price if variant else product.base_price
                order_item['unit_price']=unit_price
                total_price=quantity*unit_price
                subtotal+=total_price

            validated_data['subtotal']=subtotal
            validated_data['tax_amount']=subtotal* Decimal(0.18)
            validated_data['total_amount']=subtotal+validated_data['tax_amount']
            validated_data['user']=self.context['request'].user

        
            validated_data['discount_amount']=Decimal('0')
            if 'coupon' in validated_data and validated_data['coupon']:
        
              validated_data['discount_amount'] = subtotal * Decimal('0.10')
        
            order=models.Order.objects.create(
                **validated_data
            )
            
            models.OrderItem.objects.create(order=order,
            product=product,
            product_variant=variant,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price)

            return order

class OrderReadSerializers(serializers.ModelSerializer):

    shipping_address=AddressSerializers(read_only=True)
    billing_address=AddressSerializers(read_only=True)
    items=OrderItemSerializer(read_only=True,many=True)

    class Meta:
        model=models.Order
        fields=['items','shipping_address','billing_address','subtotal','discount_amount',
                'shipping_cost','tax_amount','total_amount','coupon','status','order_date']


class PaymentSerializers(serializers.ModelSerializer):

    class Meta:
        model= models.Payment
        fields=["payment_method"]
    