from rest_framework.permissions import BasePermission

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
        print(obj.seller.user,request.user)
        return obj.seller.user==request.user
    
class IsAdminOrReadonly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
           return True
        if request.method in ('GET','OPTIONS','HEAD'):
            return True

