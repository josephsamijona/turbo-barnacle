# Generated manually
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_remove_assignment_client'),  # Ajustez selon votre dernière migration
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('type', models.CharField(choices=[
                    ('INCOME', 'Income'), 
                    ('EXPENSE', 'Expense'), 
                    ('INTERNAL', 'Internal Transfer')
                ], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField()),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app.user')),
            ],
        ),
        migrations.AddIndex(
            model_name='financialtransaction',
            index=models.Index(fields=['transaction_id'], name='ft_transaction_id_idx'),
        ),
        migrations.AddIndex(
            model_name='financialtransaction',
            index=models.Index(fields=['type', 'date'], name='ft_type_date_idx'),
        ),
    ]