from rest_framework import serializers


class ChatSerializer(serializers.Serializer):

    message = serializers.CharField(max_length=2000)

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("A mensagem nao pode estar vazia.")
        return value