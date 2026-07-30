from rest_framework import serializers

from .models import Category

from .models import Category

class CategorySerializer(serializers.ModelSerializer):


    class Meta:
        model = Category

        fields = [
            "id",
            "name",
            "color",
            "type",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]