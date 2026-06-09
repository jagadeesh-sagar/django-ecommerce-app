from django.test import TestCase
from django.contrib.auth import get_user_model
from user.models import Product, ProductVariant, Category, Brand, Cart, CartItem, Whishlist, Review, Order, OrderItem
from inventory.models import Seller
from user.serializers import CartItemCreateSerializers
from rest_framework.exceptions import ValidationError
from django.test import RequestFactory

User = get_user_model()

class UserRoleTest(TestCase):
    def test_role_helpers(self):
        buyer = User.objects.create_user(username='buyer_user', password='pass', role_model='buyer')
        seller = User.objects.create_user(username='seller_user', password='pass', role_model='seller')

        self.assertTrue(buyer.is_buyer())
        self.assertFalse(buyer.is_seller())

        self.assertTrue(seller.is_seller())
        self.assertFalse(seller.is_buyer())

class CartSerializerTest(TestCase):
    def setUp(self):
        self.buyer_user = User.objects.create_user(username='buyer_user', password='pass', role_model='buyer')
        self.seller_user = User.objects.create_user(username='seller_user', password='pass', role_model='seller')
        self.seller = Seller.objects.create(user=self.seller_user, business_name='Business', gst_number='123456789012345')
        self.category = Category.objects.create(name='Electronics')
        self.brand = Brand.objects.create(name='Samsung')
        self.product = Product.objects.create(
            seller=self.seller,
            name='S23',
            base_price=50000.00,
            category=self.category,
            brand=self.brand,
            stock_qty=10,
            sku='S23-BASE'
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color='Blue',
            size='128GB',
            price=55000.00,
            stock_qty=5,
            sku='S23-BLUE-128'
        )

    def test_cart_item_serializer_validation(self):
        # 1. Valid addition without variant
        serializer = CartItemCreateSerializers(data={
            'product': self.product.id,
            'quantity': 5
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # 2. Exceeded stock without variant
        serializer = CartItemCreateSerializers(data={
            'product': self.product.id,
            'quantity': 15
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertTrue(any("items available" in str(err) for err in serializer.errors['non_field_errors']))

        # 3. Valid addition with variant
        serializer = CartItemCreateSerializers(data={
            'product': self.product.id,
            'product_variant': self.variant.id,
            'quantity': 3
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # 4. Exceeded stock with variant
        serializer = CartItemCreateSerializers(data={
            'product': self.product.id,
            'product_variant': self.variant.id,
            'quantity': 8
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertTrue(any("items available" in str(err) for err in serializer.errors['non_field_errors']))

class CartAndWishlistViewsTest(TestCase):
    def setUp(self):
        self.buyer_user = User.objects.create_user(username='buyer_user', password='pass', role_model='buyer')
        self.seller_user = User.objects.create_user(username='seller_user', password='pass', role_model='seller')
        self.seller = Seller.objects.create(user=self.seller_user, business_name='Business', gst_number='123456789012345')
        self.category = Category.objects.create(name='Electronics')
        self.brand = Brand.objects.create(name='Samsung')
        self.product = Product.objects.create(
            seller=self.seller,
            name='S23',
            base_price=50000.00,
            category=self.category,
            brand=self.brand,
            stock_qty=10,
            sku='S23-BASE'
        )

    def test_wishlist_deletion(self):
        Whishlist.objects.create(user=self.buyer_user, product=self.product)
        self.client.force_login(self.buyer_user)
        response = self.client.delete(f'/user/whishlist/?q={self.product.id}')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Whishlist.objects.filter(user=self.buyer_user, product=self.product).exists())

    def test_cart_item_patch_validation(self):
        cart = Cart.objects.create(user=self.buyer_user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_login(self.buyer_user)
        
        # Test valid patch
        response = self.client.patch('/user/cart/', data={
            'product': self.product.id,
            'quantity': 5
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)

        # Test invalid patch (exceeding stock)
        response = self.client.patch('/user/cart/', data={
            'product': self.product.id,
            'quantity': 15
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)  # unchanged

class ReviewViewTest(TestCase):
    def setUp(self):
        self.buyer_user = User.objects.create_user(username='buyer_user', password='pass', role_model='buyer')
        self.other_buyer = User.objects.create_user(username='other_buyer', password='pass', role_model='buyer')
        self.seller_user = User.objects.create_user(username='seller_user', password='pass', role_model='seller')
        self.seller = Seller.objects.create(user=self.seller_user, business_name='Business', gst_number='123456789012345')
        self.category = Category.objects.create(name='Electronics')
        self.brand = Brand.objects.create(name='Samsung')
        self.product = Product.objects.create(
            seller=self.seller,
            name='S23',
            base_price=50000.00,
            category=self.category,
            brand=self.brand,
            stock_qty=10,
            sku='S23-BASE'
        )

    def test_review_permission_and_crud(self):
        # 1. Try to post review without delivered order -> Should get 403
        self.client.force_login(self.buyer_user)
        response = self.client.post(f'/user/product/detail/review/?q={self.product.id}', data={
            'rating': 5,
            'review_text': 'Great phone!'
        })
        self.assertEqual(response.status_code, 403)

        # 2. Try to post review with order that is not 'delivered' -> Should get 403
        order = Order.objects.create(
            user=self.buyer_user,
            order_number='ORD-123',
            subtotal=50000.00,
            tax_amount=9000.00,
            total_amount=59000.00,
            status='processing'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=50000.00,
            total_price=50000.00
        )
        response = self.client.post(f'/user/product/detail/review/?q={self.product.id}', data={
            'rating': 5,
            'review_text': 'Great phone!'
        })
        self.assertEqual(response.status_code, 403)

        # 3. Mark order as 'delivered' -> Should succeed (201) and set is_verified_purchase = True
        order.status = 'delivered'
        order.save()
        response = self.client.post(f'/user/product/detail/review/?q={self.product.id}', data={
            'rating': 5,
            'review_text': 'Great phone!'
        })
        self.assertEqual(response.status_code, 201)
        review = Review.objects.get(user=self.buyer_user, product=self.product)
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_verified_purchase)

        # 4. Try to edit/patch the review -> Should succeed (200)
        response = self.client.patch(f'/user/product/detail/review/?q={self.product.id}', data={
            'rating': 4,
            'review_text': 'Actually, it is a 4-star phone.'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.rating, 4)

        # 5. Other user without delivered purchase tries to patch/delete -> Should get 403
        self.client.force_login(self.other_buyer)
        response = self.client.patch(f'/user/product/detail/review/?q={self.product.id}', data={
            'rating': 1
        }, content_type='application/json')
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(f'/user/product/detail/review/?q={self.product.id}')
        self.assertEqual(response.status_code, 403)

        # 6. Original buyer deletes review -> Should succeed (200)
        self.client.force_login(self.buyer_user)
        response = self.client.delete(f'/user/product/detail/review/?q={self.product.id}')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Review.objects.filter(user=self.buyer_user, product=self.product).exists())
