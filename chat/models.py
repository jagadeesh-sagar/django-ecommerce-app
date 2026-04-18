from django.db import models
from django.contrib.auth import get_user_model

User=get_user_model()

class ChatMessage(models.Model):
    order=models.ForeignKey(
        "user.Order",
        on_delete=models.CASCADE,
        related_name="chat_messages"    
    )
    sender=models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"

    )
    message=models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp=models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering=["timestamp"]
    
    def __str__(self):
        return  f"[Order {self.order_id}] {self.sender.username}: {self.message[:40]}"