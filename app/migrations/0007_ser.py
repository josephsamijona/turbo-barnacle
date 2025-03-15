from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        # Cette migration doit dépendre de celle qui crée les modèles référencés
        # Ajustez selon votre structure de migrations actuelle
        ('app', '0006_service'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('tax_amount', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('total_amount', models.DecimalField(max_digits=10, decimal_places=2)),
                
                ('payment_method', models.CharField(max_length=50, choices=[
                    # Méthodes bancaires traditionnelles
                    ('CREDIT_CARD', _('Credit Card')),
                    ('DEBIT_CARD', _('Debit Card')),
                    ('BANK_TRANSFER', _('Bank Transfer')),
                    ('ACH', _('ACH')),
                    ('CHECK', _('Check')),
                    ('CASH', _('Cash')),
                    
                    # Services de paiement numérique US
                    ('ZELLE', _('Zelle')),
                    ('VENMO', _('Venmo')),
                    ('CASH_APP', _('Cash App')),
                    ('PAYPAL', _('PayPal')),
                    
                    # Portefeuilles mobiles
                    ('APPLE_PAY', _('Apple Pay')),
                    ('GOOGLE_PAY', _('Google Pay')),
                    ('SAMSUNG_PAY', _('Samsung Pay')),
                    
                    # Services de transfert internationaux
                    ('WESTERN_UNION', _('Western Union')),
                    ('MONEY_GRAM', _('MoneyGram')),
                    ('TAPTP_SEND', _('Tap Tap Send')),
                    ('REMITLY', _('Remitly')),
                    ('WORLDREMIT', _('WorldRemit')),
                    ('XOOM', _('Xoom')),
                    ('WISE', _('Wise (TransferWise)')),
                    
                    # Plateformes de paiement
                    ('STRIPE', _('Stripe')),
                    ('SQUARE', _('Square')),
                    
                    # Crypto-monnaies
                    ('CRYPTO_BTC', _('Bitcoin')),
                    ('CRYPTO_ETH', _('Ethereum')),
                    ('CRYPTO_USDT', _('USDT')),
                    
                    # Autres
                    ('OTHER', _('Other')),
                ])),
                
                ('status', models.CharField(max_length=20, choices=[
                    ('PENDING', _('Pending')),
                    ('PROCESSING', _('Processing')),
                    ('COMPLETED', _('Completed')),
                    ('FAILED', _('Failed')),
                    ('REFUNDED', _('Refunded')),
                    ('CANCELLED', _('Cancelled')),
                    ('DISPUTED', _('Disputed')),
                ])),
                
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('due_date', models.DateTimeField(null=True, blank=True)),
                ('completed_date', models.DateTimeField(null=True, blank=True)),
                
                ('invoice_number', models.CharField(max_length=50, unique=True)),
                ('payment_proof', models.FileField(upload_to='payment_proofs/', null=True, blank=True)),
                ('external_reference', models.CharField(max_length=100, blank=True, null=True)),
                
                ('notes', models.TextField(blank=True, null=True)),
                
                # Relations avec d'autres modèles
                ('transaction', models.OneToOneField(on_delete=models.PROTECT, to='app.FinancialTransaction')),
                ('client', models.ForeignKey(on_delete=models.PROTECT, to='app.Client')),
                ('assignment', models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, to='app.Assignment')),
                ('quote', models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, to='app.Quote')),
            ],
        ),
    ]