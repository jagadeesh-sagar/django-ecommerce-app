from django.urls import path
from .views import ChatHistoryView

urlpatterns = [
    path("orders/<int:order_id>/chat/", ChatHistoryView.as_view()),
]