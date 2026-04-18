from rest_framework.permissions import BasePermission
from .models import Order,OrderItem

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
        print(obj)
        return request.user.is_authenticated and obj.product.seller.user==request.user
    
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
    