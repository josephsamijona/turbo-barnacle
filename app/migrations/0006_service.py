from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        # Assurez-vous de remplacer 'your_app_name' avec le nom de votre application
        # et '0004_previous_migration' avec le nom de votre précédente migration
        # Note: Cette migration doit être créée AVANT la migration Service, car Service
        # dépend de PayrollDocument
        ('app', '0005_expenses'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayrollDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # Company Information
                ('company_logo', models.ImageField(blank=True, upload_to='company_logos/')),
                ('company_address', models.CharField(blank=True, max_length=255)),
                ('company_phone', models.CharField(blank=True, max_length=20)),
                ('company_email', models.EmailField(blank=True, max_length=254)),
                
                # Interpreter Information
                ('interpreter_name', models.CharField(blank=True, max_length=100)),
                ('interpreter_address', models.CharField(blank=True, max_length=255)),
                ('interpreter_phone', models.CharField(blank=True, max_length=20)),
                ('interpreter_email', models.EmailField(blank=True, max_length=254)),
                
                # Document Information
                ('document_number', models.CharField(max_length=50, unique=True)),
                ('document_date', models.DateField()),
                
                # Payment Information (Optional)
                ('bank_name', models.CharField(blank=True, max_length=100, null=True)),
                ('account_number', models.CharField(blank=True, max_length=50, null=True)),
                ('routing_number', models.CharField(blank=True, max_length=50, null=True)),
                
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]