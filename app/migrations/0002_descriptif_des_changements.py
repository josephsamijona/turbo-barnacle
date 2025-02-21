# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),  # Remplacez XXXX par le numéro de votre migration précédente
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='client_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='client_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='client_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='is_paid',
            field=models.BooleanField(blank=True, help_text='Indicates if the assignment has been paid', null=True),
        ),
    ]