from . import views,cart_views,order_views,payment_views,product_views,seller_views
from django.urls import path,include

urlpatterns=[
    
    path('products/',product_views.product_list_view,name='product-list'),
    path('product/create/',product_views.product_create_view,name='product-create'),
    path('product/detail/<int:pk>',product_views.product_detail_view,name='product-detail'),
    path('product/search/',product_views.product_search_view,name='product-search'),
    path('product/image/',product_views.productImage_retrieve_view,name='product-image'),
    path('product/categories/',views.category_view,name='category-create'),
    path('product/detail/review/',views.review_list_view,name='product-review'),
    path('product/seller-ans/<int:pk>',seller_views.seller_ans_view,name='qna-ans'),
    path('product/customer-qxn/',views.customer_qxns_view,name='qna'),
    path('address/',views.address_create_view,name='address-create'),
    path('cart/',cart_views.cartitem_view,name='cart-item'),
    path('brand/',views.brand_list_create_view,name='brands'),
    path('whishlist/',cart_views.wishlist_view,name='whishlist'),
    path('order/',order_views.order_list_create_view,name='order'),
    path('payment/',payment_views.payment_list_create_view,name='payment'),
]