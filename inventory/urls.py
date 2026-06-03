from . import views
from django.urls import path,include

urlpatterns=[

    path('registration/',views.SellerRegister_view,name='seller-register'),

]