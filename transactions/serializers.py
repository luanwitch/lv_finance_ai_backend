from rest_framework import serializers

from .categories import CATEGORY_MAP, CATEGORY_SLUGS
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    category_detail = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "id",
            "title",
            "amount",
            "category",
            "category_fk",
            "category_detail",
            "type",
            "date",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "O valor deve ser maior que zero."
            )

        return value

    def validate_category(self, value):
        slug = (value or "").strip().lower()

        if not slug:
            return ""

        if slug not in CATEGORY_SLUGS:
            raise serializers.ValidationError("Categoria desconhecida.")

        return slug

    def validate_category_fk(self, value):
        if value is None:
            return value

        request = self.context.get("request")

        if request is not None and value.user_id != request.user.id:
            raise serializers.ValidationError("Categoria invalida.")

        return value

    def create(self, validated_data):
        user = validated_data.get("user")
        self._sync_category_fk(validated_data, user)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = validated_data.get("user", instance.user)
        self._sync_category_fk(validated_data, user)
        return super().update(instance, validated_data)

    def _sync_category_fk(self, validated_data, user):
        """Mantem category_fk coerente com o slug de `category`.

        - Se `category` for informado, resolve para a categoria canonica do
          usuario (criando se necessario) e sobrescreve `category_fk`,
          garantindo consistencia interna do registro.
        - Se apenas `category_fk` for informado, mantém o valor validado.
        """
        slug = validated_data.get("category")

        if not slug:
            return

        name, icon, cat_type = CATEGORY_MAP[slug]

        from categories.models import Category

        category, _ = Category.objects.get_or_create(
            user=user,
            name=name,
            defaults={"icon": icon, "type": cat_type},
        )

        validated_data["category_fk"] = category

    def get_category_detail(self, obj):
        category = obj.category_fk

        if category is None:
            return None

        return {
            "id": category.id,
            "name": category.name,
            "icon": category.icon,
            "color": category.color,
            "type": category.type,
        }
