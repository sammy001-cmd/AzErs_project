from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_ticketpurchase_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="brand",
            name="account_number",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="brand",
            name="bank_name",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
