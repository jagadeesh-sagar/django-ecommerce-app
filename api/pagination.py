from rest_framework.pagination import LimitOffsetPagination,CursorPagination,PageNumberPagination


class StandardPagination(PageNumberPagination):
    '''
    use for handling pagination for apiview
    '''
    page_size=5
    max_page_size=20

class StandardLimitOffset(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100

class ProductCursorPagination(CursorPagination): 
    '''
    Use Cursor for feeds, timelines, infinite scroll — anything real-time
    where new data is constantly being inserted (like an order feed or notification list)
    
    '''
    page_size = 3
    ordering = '-created_at'  # required — must specify ordering
    