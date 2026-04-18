from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()

    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "message", "timestamp"]