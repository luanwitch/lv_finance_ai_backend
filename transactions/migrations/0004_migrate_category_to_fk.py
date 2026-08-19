from django.db import migrations


def migrate_category_strings_to_fk(apps, schema_editor):
    Transaction = apps.get_model("transactions", "Transaction")
    Category = apps.get_model("categories", "Category")

    CATEGORY_MAP = {
        "salario": ("Salário", "💼", "income"),
        "alimentacao": ("Alimentação", "🍽️", "expense"),
        "transporte": ("Transporte", "🚗", "expense"),
        "moradia": ("Moradia", "🏠", "expense"),
        "saude": ("Saúde", "💊", "expense"),
        "educacao": ("Educação", "📚", "expense"),
        "lazer": ("Lazer", "🎉", "expense"),
        "investimentos": ("Investimentos", "📈", "expense"),
        "outros": ("Outros", "✨", "expense"),
    }

    for tx in Transaction.objects.select_related("user").all():
        cat_str = tx.category.strip().lower() if tx.category else ""

        if not cat_str:
            continue

        if cat_str not in CATEGORY_MAP:
            cat_str = "outros"

        name, icon, cat_type = CATEGORY_MAP[cat_str]

        category, _ = Category.objects.get_or_create(
            user=tx.user,
            name=name,
            defaults={"icon": icon, "type": cat_type},
        )

        tx.category_fk = category
        tx.save(update_fields=["category_fk"])


def reverse_migration(apps, schema_editor):
    Transaction = apps.get_model("transactions", "Transaction")
    Transaction.objects.all().update(category_fk=None)


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0003_remove_transaction_transaction_categor_d2bef2_idx_and_more"),
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            migrate_category_strings_to_fk,
            reverse_migration,
        ),
    ]
