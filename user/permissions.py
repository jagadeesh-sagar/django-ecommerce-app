from rest_framework.permissions import BasePermission
from .models import Order,OrderItem,Product

class IsSeller(BasePermission):
    '''
        only sellers can perfom this action
    '''

    def has_permission(self,request,view):
        return request.user.is_authenticated and request.user.role_model=='seller'
    
class IsBuyer(BasePermission):
    '''
        only buyers can perfom this action
    '''

    def has_permission(self, request, view):
        return  request.user.is_authenticated and request.user.role_model=="buyer"
    
class IsSellerOrReadOnly(BasePermission):
    '''
    sellers can write and other's can just read
    '''

    def has_permission(self, request, view):

        if request.method in ('GET','HEAD','OPTIONS'):
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role_model=='seller'
    

class IsProductOwner(BasePermission):
    '''
    only Product owner can perfom this action
    '''

    def has_object_permission(self, request, view, obj):
    
        return request.user.is_authenticated and obj.seller.user==request.user
    
class IsAdminOrReadonly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
           return True
        if request.method in ('GET','OPTIONS','HEAD'):
            return True


class IsOrderParticipant(BasePermission):
    """
    Only buyer or seller of the order can access
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        order_id = view.kwargs.get("order_id")

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return False

        # buyer
        if request.user.id == order.user_id:
            return True

        # seller (any item in order)
        return OrderItem.objects.filter(
            order_id=order_id,
            product__seller_id=request.user.id
        ).exists()
    

class IsDeliveredProductBuyer(BasePermission):
    """
    Only buyers who purchased the product and whose order/shipment status is delivered can review.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        product_id = request.GET.get('q')
        if not product_id:
            product_id = request.data.get('product') or request.data.get('product_id')

        if not product_id:
            return False

        # Order status delivered
        delivered_order_exists = Order.objects.filter(
            user=request.user,
            status='delivered',
            items__product_id=product_id
        ).exists()

        # Shipment status delivered
        delivered_shipment_exists = Order.objects.filter(
            user=request.user,
            items__product_id=product_id,
            shipment__status='delivered'
        ).exists()

        return delivered_order_exists or delivered_shipment_exists
    