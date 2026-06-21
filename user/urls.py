from . import views,cart_views,order_views,payment_views,product_views,seller_views
from django.urls import path,include

urlpatterns=[

    path('ai/',views.anthropic_proxy_view,name='anthropic-proxy'),
    path('products/',product_views.product_list_view,name='product-list'),
    path('product/create/',product_views.product_create_view,name='product-create'),
    path('product/detail/<int:pk>',product_views.product_detail_view,name='product-detail'),
    path('product/delete/<int:product>/',product_views.product_delete_view,name='product-delete'),
    path('product/delete/<int:product>/<int:variant>/',product_views.product_delete_view,name='product-variant-delete'),
    path('product/search/',product_views.product_search_view,name='product-search'),
    path('product/image/',product_views.productImage_retrieve_view,name='product-image'),
    path('product/categories/',views.category_view,name='category-create'),
    path('product/detail/review/',views.review_list_view,name='product-review'),
    path('review/media/',views.review_media_view,name='review-media'),
    path('product/seller-ans/<int:pk>',seller_views.seller_ans_view,name='qna-ans'),
    path('product/customer-qxn/',views.customer_qxns_view,name='qna'),
    path('address/',views.address_create_view,name='address-create'),
    path('cart/',cart_views.cartitem_view,name='cart-item'),
    path('brand/',views.brand_list_create_view,name='brands'),
    path('whishlist/',cart_views.wishlist_view,name='whishlist'),
    path('order/',order_views.order_list_create_view,name='order'),
    path('order-item/<int:pk>/status/', order_views.order_item_status_update_view, name='order-item-status-update'),
    path('seller/orders/', order_views.seller_order_list_view),
    path("payments/cod/", payment_views.CashOnDeliveryView.as_view()),        
    path("payments/cod/<int:order_id>/confirm/", payment_views.ConfirmCODPaymentView.as_view()),
    path("payments/create/", payment_views.CreateRazorpayOrderView.as_view()),
    path("payments/verify/", payment_views.VerifyPaymentView.as_view()),

]