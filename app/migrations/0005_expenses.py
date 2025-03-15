from django.db import migrations, models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # Assurez-vous de remplacer 'your_app_name' avec le nom de votre application
        # et '0004_previous_migration' avec le nom de votre 4ème migration
        ('app', '0003_create_interpreter_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expense_type', models.CharField(choices=[
                    ('OPERATIONAL', _('Operational')),
                    ('ADMINISTRATIVE', _('Administrative')),
                    ('MARKETING', _('Marketing')),
                    ('SALARY', _('Salary')),
                    ('TAX', _('Tax')),
                    ('OTHER', _('Other'))
                ], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[
                    ('PENDING', _('Pending')),
                    ('APPROVED', _('Approved')),
                    ('PAID', _('Paid')),
                    ('REJECTED', _('Rejected'))
                ], max_length=20)),
                ('date_incurred', models.DateTimeField()),
                ('date_paid', models.DateTimeField(blank=True, null=True)),
                ('receipt', models.FileField(blank=True, null=True, upload_to='expense_receipts/')),
                ('notes', models.TextField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('transaction', models.OneToOneField(on_delete=models.PROTECT, to='app.FinancialTransaction')),
            ],
        ),
    ]