import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatMessage


class OrderChatConsumer(AsyncWebsocketConsumer):
    '''
    Authenticated user(buyer) and seller(Product Owner) Allowed:
        to chat

    '''

    async def connect(self):
        self.order_id=self.scope['url_route']['kwargs']['order_id']
        self.room_group_name=f"order_chat_{self.order_id}"
        self.user=self.scope["user"]

        if isinstance(self.user,AnonymousUser):
            await self.close(code=4001)
            return 
        
        allowed=await self.is_participant()
        print(f"User {self.user.username} allowed for order {self.order_id}: {allowed}")

        if not allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        history=await self.get_chat_history()
        await self.send(text_data=json.dumps({
            "type":"history",
            "message":history
        }))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data=json.loads(text_data)
        message=data.get("message","").strip()

        if not message:
            return

        saved=await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type":"chat_message",
                "message":message,
                "sender":self.user.username,
                "timestamp":saved.timestamp.isoformat(),
                "sender_id":self.user.id,
            }
        )

        if data.get("type")=="typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type":"typing_event",
                    "user":self.user.username,
                    "is_typing":data["is_typing"],
                }
            )
        if data.get("type")=="read":
            await self.mark_as_read(data['message_id'])

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type":"read_event",
                    "message_id":data["message_id"],
                    "user":self.user.username

                }

            )
    
    # --- DB helpers (sync → async) ---

    @database_sync_to_async
    def is_participant(self):
        from user.models import OrderItem
        try:
            orderitem = OrderItem.objects.select_related(
                "order__user", "product__seller"
            ).filter(order_id=self.order_id).first() 
            
            if not orderitem:
                return False
                
            return self.user.id in (orderitem.order.user_id, orderitem.product.seller.user.id)

        except Exception as e:
            print(f"is_participant error: {e}")  
            return False
        
    @database_sync_to_async
    def save_message(self,message):
        return ChatMessage.objects.create(
            order_id=self.order_id,
            sender=self.user,
            message=message,
        )

    @database_sync_to_async
    def get_chat_history(self):
        messages = ChatMessage.objects.filter(
            order_id=self.order_id
        ).select_related("sender").order_by("-timestamp")[:20]

        return [
        {
                "message": m.message,
                "sender": m.sender.username,
                "sender_id": m.sender_id,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in reversed(list(messages))
        ]
    
    @database_sync_to_async
    def mark_as_read(self, message_id):
        from .models import ChatMessage
        ChatMessage.objects.filter(id=message_id).update(is_read=True)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "sender": event["sender"],
            "sender_id": event["sender_id"],
            "timestamp": event["timestamp"],
        }))

    async def typing_event(self,event):
        await self.send(text_data=json.dumps({
            "type":"typing",
            "user":event["user"],
            "is_typing":event["is_typing"]
        }))

    async def read_event(self,event):
        await self.send(text_data=json.dumps({
            "type":"read",
            "message_id":event["message_id"],
            "user":event["user"],
        }))