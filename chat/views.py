from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated,AllowAny ,BasePermission
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from user.models import OrderItem,Order
from user.permissions import IsOrderParticipant


class ChatHistoryView(ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsOrderParticipant]

    def get_queryset(self):
        order_id = self.kwargs["order_id"]

        return ChatMessage.objects.filter(
            order_id=order_id
        ).select_related("sender").order_by("-timestamp")