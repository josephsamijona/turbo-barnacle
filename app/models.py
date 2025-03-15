import decimal
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # ISO code
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Languagee(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # ISO code
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class User(AbstractUser):
    class Roles(models.TextChoices):
        CLIENT = 'CLIENT', _('Client')
        INTERPRETER = 'INTERPRETER', _('Interprète')
        ADMIN = 'ADMIN', _('Administrateur')

    # Ajout des related_name pour éviter les conflits
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set'  # Ajout du related_name personnalisé
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set'  # Ajout du related_name personnalisé
    )

    email = models.EmailField(unique=True)
    # Dans models.py, classe User
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name=_('Phone number')
    )
    role = models.CharField(max_length=20, choices=Roles.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    registration_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True, null=True)  # Nouveau champ ajouté
    email = models.EmailField(blank=True, null=True)  # Nouveau champ ajouté
    billing_address = models.TextField(blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_state = models.CharField(max_length=50, blank=True, null=True)
    billing_zip_code = models.CharField(max_length=20, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    preferred_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

class InterpreterLanguage(models.Model):
    class Proficiency(models.TextChoices):
        NATIVE = 'NATIVE', _('Natif')
        FLUENT = 'FLUENT', _('Courant')
        PROFESSIONAL = 'PROFESSIONAL', _('Professionnel')
        INTERMEDIATE = 'INTERMEDIATE', _('Intermédiaire')

    interpreter = models.ForeignKey('Interpreter', on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    proficiency = models.CharField(max_length=20, choices=Proficiency.choices)
    is_primary = models.BooleanField(default=False)
    certified = models.BooleanField(default=False)
    certification_details = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['interpreter', 'language']

class Interpreter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='interpreter_profile')
    languages = models.ManyToManyField(Language, through=InterpreterLanguage)
    profile_image = models.ImageField(upload_to='interpreter_profiles/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    certifications = models.JSONField(null=True, blank=True)  # Format: [{"name": "CCHI", "expiry_date": "2025-01-01"}]
    specialties = models.JSONField(null=True, blank=True)  # Format: ["Medical", "Legal"]
    availability = models.JSONField(null=True, blank=True)  # Format: {"monday": ["9:00-17:00"]}
    radius_of_service = models.IntegerField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    
    
    # Informations bancaires pour ACH
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_holder_name = models.CharField(max_length=100, null=True, blank=True)
    routing_number = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=100, null=True, blank=True)
    account_type = models.CharField(
        max_length=10, 
        choices=[('checking', 'Checking'), ('savings', 'Savings')],
        null=True,
        blank=True
    )
    
    background_check_date = models.DateField(null=True, blank=True)
    background_check_status = models.BooleanField(default=False)
    w9_on_file = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

# models.py
class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_hours = models.IntegerField(default=1)
    cancellation_policy = models.TextField()
    requires_certification = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class QuoteRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        QUOTED = 'QUOTED', _('Quoted')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
        EXPIRED = 'EXPIRED', _('Expired')

    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    requested_date = models.DateTimeField()
    duration = models.IntegerField(help_text="Durée en minutes")
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    source_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='quote_requests_source')
    target_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='quote_requests_target')
    special_requirements = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Quote(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        SENT = 'SENT', _('Sent')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
        EXPIRED = 'EXPIRED', _('Expired')
        CANCELLED = 'CANCELLED', _('Cancelled')

    quote_request = models.OneToOneField(QuoteRequest, on_delete=models.PROTECT)
    reference_number = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_until = models.DateField()
    terms = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Assignment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')  # Assigné à un interprète, en attente de confirmation
        CONFIRMED = 'CONFIRMED', _('Confirmed')  # Accepté par l'interprète
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')  # Mission en cours
        COMPLETED = 'COMPLETED', _('Completed')  # Mission terminée
        CANCELLED = 'CANCELLED', _('Cancelled')  # Refusé par l'interprète
        NO_SHOW = 'NO_SHOW', _('No Show')  # Client ou interprète absent

    # Relations existantes
    quote = models.OneToOneField(Quote, on_delete=models.PROTECT, null=True, blank=True)
    interpreter = models.ForeignKey(
        Interpreter, 
        on_delete=models.SET_NULL,  # Au lieu de PROTECT
        null=True, 
        blank=True
    )
    
    # Client fields - all optional
    client_name = models.CharField(max_length=255, null=True, blank=True)  
    client_email = models.EmailField(null=True, blank=True)  
    client_phone = models.CharField(max_length=20, null=True, blank=True)  
    
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    source_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='assignments_source')
    target_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='assignments_target')
    
    # Champs temporels et localisation
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=Status.choices)
    # Ajouter ce champ après les champs financiers existants:
    is_paid = models.BooleanField(null=True, blank=True, help_text="Indicates if the assignment has been paid")
    
    # Informations financières
    interpreter_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Taux horaire de l'interprète")
    minimum_hours = models.IntegerField(default=2)
    total_interpreter_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Informations additionnelles
    notes = models.TextField(blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'interpreter', 'start_time']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        client_info = self.client_name or "Unspecified Client"
        return f"Assignment {self.id} - {client_info} ({self.status})"

    # Remove the clean method entirely or replace with one that has no client validations
    # def clean(self):
    #    """Validation personnalisée simplifiée"""
    #    # Suppression complète des validations client
    #    pass

    def save(self, *args, **kwargs):
        # No validation required for client fields
        super().save(*args, **kwargs)

    def can_be_confirmed(self):
        """Vérifie si l'assignment peut être confirmé"""
        return self.status == self.Status.PENDING

    def can_be_started(self):
        """Vérifie si l'assignment peut être démarré"""
        return self.status == self.Status.CONFIRMED

    def can_be_completed(self):
       """Vérifie si l'assignment peut être marqué comme terminé"""
       return self.status in [self.Status.IN_PROGRESS, self.Status.CONFIRMED]

    def can_be_cancelled(self):
        """Vérifie si l'assignment peut être annulé"""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    def confirm(self):
        """Confirme l'assignment"""
        if self.can_be_confirmed():
            self.status = self.Status.CONFIRMED
            self.save()
            return True
        return False

    def start(self):
        """Démarre l'assignment"""
        if self.can_be_started():
            self.status = self.Status.IN_PROGRESS
            self.save()
            return True
        return False

    def complete(self):
        """Marque l'assignment comme terminé"""
        if self.can_be_completed():
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save()
            return True
        return False

    def cancel(self):
        """Annule l'assignment"""
        if self.can_be_cancelled():
            self.status = self.Status.CANCELLED
            old_interpreter = self.interpreter
            self.interpreter = None  # Désassociation de l'interprète
            self.save()
            return old_interpreter  # Retourne l'ancien interprète pour la notification
        return None

    def get_client_display(self):
        """Retourne les informations du client à afficher"""
        return self.client_name or "Unspecified Client"
class AssignmentFeedback(models.Model):
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')

    class PaymentType(models.TextChoices):
        CLIENT_PAYMENT = 'CLIENT_PAYMENT', _('Client Payment')
        INTERPRETER_PAYMENT = 'INTERPRETER_PAYMENT', _('Interpreter Payment')


    quote = models.ForeignKey(Quote, on_delete=models.PROTECT, null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    payment_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

class Notification(models.Model):
    class Type(models.TextChoices):
        QUOTE_REQUEST = 'QUOTE_REQUEST', _('Quote Request')
        QUOTE_READY = 'QUOTE_READY', _('Quote Ready')
        ASSIGNMENT_OFFER = 'ASSIGNMENT_OFFER', _('Assignment Offer')
        ASSIGNMENT_REMINDER = 'ASSIGNMENT_REMINDER', _('Assignment Reminder')
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', _('Payment Received')
        SYSTEM = 'SYSTEM', _('System')

    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=200)
    content = models.TextField()
    read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    
class PublicQuoteRequest(models.Model):
    # Contact Information
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company_name = models.CharField(max_length=100)
    
    # Service Details
    source_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='public_quotes_source')
    target_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='public_quotes_target')
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    requested_date = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    
    # Location
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    
    # Additional Information
    special_requirements = models.TextField(blank=True, null=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Quote Request from {self.full_name} ({self.company_name})"

# models.py

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email Notifications
    email_quote_updates = models.BooleanField(default=True, help_text="Receive email notifications about quote status updates")
    email_assignment_updates = models.BooleanField(default=True, help_text="Receive email notifications about assignment updates")
    email_payment_updates = models.BooleanField(default=True, help_text="Receive email notifications about payment status")
    
    # SMS Notifications
    sms_enabled = models.BooleanField(default=False, help_text="Enable SMS notifications")
    
    # In-App Notifications
    quote_notifications = models.BooleanField(default=True, help_text="Receive in-app notifications about quotes")
    assignment_notifications = models.BooleanField(default=True, help_text="Receive in-app notifications about assignments")
    payment_notifications = models.BooleanField(default=True, help_text="Receive in-app notifications about payments")
    system_notifications = models.BooleanField(default=True, help_text="Receive system notifications and updates")

    # Communication Preferences
    preferred_language = models.ForeignKey(
        Language, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        help_text="Preferred language for notifications"
    )
    
    # Notification Frequency
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest')
        ],
        default='immediate',
        help_text="How often to receive notifications"
    )

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Notification preferences for {self.user.email}"

    def save(self, *args, **kwargs):
        # On vérifie si l'utilisateur est un client ou un interprète
        if not self.preferred_language:
            if hasattr(self.user, 'client_profile') and self.user.client_profile:
                self.preferred_language = self.user.client_profile.preferred_language
            elif hasattr(self.user, 'interpreter_profile') and self.user.interpreter_profile:
                self.preferred_language = None
        super().save(*args, **kwargs)
        
        
class AssignmentNotification(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='notifications')
    interpreter = models.ForeignKey(Interpreter, on_delete=models.CASCADE, related_name='assignment_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['interpreter', 'is_read']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"Notification for {self.assignment} - {self.interpreter}"

    @classmethod
    def create_for_new_assignment(cls, assignment):
        """
        Crée une notification pour un nouvel assignment
        """
        return cls.objects.create(
            assignment=assignment,
            interpreter=assignment.interpreter
        )

    @classmethod
    def get_unread_count(cls, interpreter):
        """
        Retourne le nombre de notifications non lues pour un interprète
        """
        return cls.objects.filter(
            interpreter=interpreter,
            is_read=False
        ).count()

    def mark_as_read(self):
        """
        Marque la notification comme lue
        """
        self.is_read = True
        self.save()

class FinancialTransaction(models.Model):
    """Table principale pour tracer toutes les transactions financières"""
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', _('Income')
        EXPENSE = 'EXPENSE', _('Expense')
        INTERNAL = 'INTERNAL', _('Internal Transfer')

    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)

class ClientPayment(models.Model):
    """Gestion des paiements reçus des clients"""
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')
        CANCELLED = 'CANCELLED', _('Cancelled')
        DISPUTED = 'DISPUTED', _('Disputed')

    class PaymentMethod(models.TextChoices):
    # Méthodes bancaires traditionnelles
        CREDIT_CARD = 'CREDIT_CARD', _('Credit Card')
        DEBIT_CARD = 'DEBIT_CARD', _('Debit Card')
        BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
        ACH = 'ACH', _('ACH')
        CHECK = 'CHECK', _('Check')
        CASH = 'CASH', _('Cash')
        
        # Services de paiement numérique US
        ZELLE = 'ZELLE', _('Zelle')
        VENMO = 'VENMO', _('Venmo')
        CASH_APP = 'CASH_APP', _('Cash App')
        PAYPAL = 'PAYPAL', _('PayPal')
        
        # Portefeuilles mobiles
        APPLE_PAY = 'APPLE_PAY', _('Apple Pay')
        GOOGLE_PAY = 'GOOGLE_PAY', _('Google Pay')
        SAMSUNG_PAY = 'SAMSUNG_PAY', _('Samsung Pay')
        
        # Services de transfert internationaux
        WESTERN_UNION = 'WESTERN_UNION', _('Western Union')
        MONEY_GRAM = 'MONEY_GRAM', _('MoneyGram')
        TAPTP_SEND = 'TAPTP_SEND', _('Tap Tap Send')
        REMITLY = 'REMITLY', _('Remitly')
        WORLDREMIT = 'WORLDREMIT', _('WorldRemit')
        XOOM = 'XOOM', _('Xoom')
        WISE = 'WISE', _('Wise (TransferWise)')
        
        # Plateformes de paiement
        STRIPE = 'STRIPE', _('Stripe')
        SQUARE = 'SQUARE', _('Square')
        
        # Crypto-monnaies
        CRYPTO_BTC = 'CRYPTO_BTC', _('Bitcoin')
        CRYPTO_ETH = 'CRYPTO_ETH', _('Ethereum')
        CRYPTO_USDT = 'CRYPTO_USDT', _('USDT')
        
        # Autres
        OTHER = 'OTHER', _('Other')

    transaction = models.OneToOneField(FinancialTransaction, on_delete=models.PROTECT)
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, null=True, blank=True)
    quote = models.ForeignKey(Quote, on_delete=models.PROTECT, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    
    payment_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    invoice_number = models.CharField(max_length=50, unique=True)
    payment_proof = models.FileField(upload_to='payment_proofs/', null=True, blank=True)
    external_reference = models.CharField(max_length=100, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)

class InterpreterPayment(models.Model):
    """Gestion des paiements aux interprètes"""
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    class PaymentMethod(models.TextChoices):
        # Méthodes bancaires traditionnelles
        CREDIT_CARD = 'CREDIT_CARD', _('Credit Card')
        DEBIT_CARD = 'DEBIT_CARD', _('Debit Card')
        BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
        ACH = 'ACH', _('ACH')
        CHECK = 'CHECK', _('Check')
        CASH = 'CASH', _('Cash')
        
        # Services de paiement numérique US
        ZELLE = 'ZELLE', _('Zelle')
        VENMO = 'VENMO', _('Venmo')
        CASH_APP = 'CASH_APP', _('Cash App')
        PAYPAL = 'PAYPAL', _('PayPal')
        
        # Portefeuilles mobiles
        APPLE_PAY = 'APPLE_PAY', _('Apple Pay')
        GOOGLE_PAY = 'GOOGLE_PAY', _('Google Pay')
        SAMSUNG_PAY = 'SAMSUNG_PAY', _('Samsung Pay')
        
        # Services de transfert internationaux
        WESTERN_UNION = 'WESTERN_UNION', _('Western Union')
        MONEY_GRAM = 'MONEY_GRAM', _('MoneyGram')
        TAPTP_SEND = 'TAPTP_SEND', _('Tap Tap Send')
        REMITLY = 'REMITLY', _('Remitly')
        WORLDREMIT = 'WORLDREMIT', _('WorldRemit')
        XOOM = 'XOOM', _('Xoom')
        WISE = 'WISE', _('Wise (TransferWise)')
        
        # Plateformes de paiement
        STRIPE = 'STRIPE', _('Stripe')
        SQUARE = 'SQUARE', _('Square')
        
        # Crypto-monnaies
        CRYPTO_BTC = 'CRYPTO_BTC', _('Bitcoin')
        CRYPTO_ETH = 'CRYPTO_ETH', _('Ethereum')
        CRYPTO_USDT = 'CRYPTO_USDT', _('USDT')
        
        # Autres
        OTHER = 'OTHER', _('Other')

    # Relations
    transaction = models.OneToOneField('FinancialTransaction', on_delete=models.PROTECT)
    interpreter = models.ForeignKey('Interpreter', on_delete=models.PROTECT)
    assignment = models.ForeignKey('Assignment', on_delete=models.PROTECT, null=True, blank=True)
    
    # Informations de paiement
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Dates
    scheduled_date = models.DateTimeField()
    processed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)
    
    # Informations supplémentaires
    reference_number = models.CharField(max_length=50, unique=True)
    payment_proof = models.FileField(upload_to='interpreter_payment_proofs/', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Interpreter Payment'
        verbose_name_plural = 'Interpreter Payments'
        indexes = [
            models.Index(fields=['status', 'scheduled_date'], name='ip_status_scheduled_idx'),
            models.Index(fields=['interpreter', 'status'], name='ip_interpreter_status_idx'),
            models.Index(fields=['created_at'], name='ip_created_at_idx'),
        ]

    def __str__(self):
        return f"Payment {self.reference_number} - {self.interpreter}"

    def clean(self):
        """Validation personnalisée"""
        if self.status == self.Status.COMPLETED and not self.processed_date:
            raise ValidationError({
                'processed_date': 'Processed date is required when status is completed'
            })

    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour validation"""
        self.clean()
        super().save(*args, **kwargs)

    def can_be_processed(self):
        """Vérifie si le paiement peut être traité"""
        return self.status == self.Status.PENDING

    def can_be_completed(self):
        """Vérifie si le paiement peut être marqué comme complété"""
        return self.status == self.Status.PROCESSING

    def mark_as_processing(self):
        """Marque le paiement comme en cours de traitement"""
        if self.can_be_processed():
            self.status = self.Status.PROCESSING
            self.save()
            return True
        return False

    def mark_as_completed(self):
        """Marque le paiement comme complété"""
        if self.can_be_completed():
            self.status = self.Status.COMPLETED
            self.processed_date = timezone.now()
            self.save()
            return True
        return False

    def mark_as_failed(self):
        """Marque le paiement comme échoué"""
        if self.status in [self.Status.PENDING, self.Status.PROCESSING]:
            self.status = self.Status.FAILED
            self.save()
            return True
        return False
    
class Expense(models.Model):
    """Gestion des dépenses de l'entreprise"""
    class ExpenseType(models.TextChoices):
        OPERATIONAL = 'OPERATIONAL', _('Operational')
        ADMINISTRATIVE = 'ADMINISTRATIVE', _('Administrative')
        MARKETING = 'MARKETING', _('Marketing')
        SALARY = 'SALARY', _('Salary')
        TAX = 'TAX', _('Tax')
        OTHER = 'OTHER', _('Other')

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        PAID = 'PAID', _('Paid')
        REJECTED = 'REJECTED', _('Rejected')

    transaction = models.OneToOneField(FinancialTransaction, on_delete=models.PROTECT)
    expense_type = models.CharField(max_length=20, choices=ExpenseType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    
    status = models.CharField(max_length=20, choices=Status.choices)
    date_incurred = models.DateTimeField()
    date_paid = models.DateTimeField(null=True, blank=True)
    
    receipt = models.FileField(upload_to='expense_receipts/', null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    
 
   
class PayrollDocument(models.Model):
    # Company Information
    company_logo = models.ImageField(upload_to='company_logos/', blank=True)
    company_address = models.CharField(max_length=255, blank=True)
    company_phone = models.CharField(max_length=20, blank=True)
    company_email = models.EmailField(blank=True)

    # Interpreter Information
    interpreter_name = models.CharField(max_length=100, blank=True)
    interpreter_address = models.CharField(max_length=255, blank=True)
    interpreter_phone = models.CharField(max_length=20, blank=True)
    interpreter_email = models.EmailField(blank=True)

    # Document Information
    document_number = models.CharField(max_length=50, unique=True)
    document_date = models.DateField()

    # Payment Information (Optional)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    routing_number = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payroll {self.document_number} - {self.interpreter_name}"

class Service(models.Model):
    payroll = models.ForeignKey(PayrollDocument, on_delete=models.CASCADE, related_name='services')
    date = models.DateField(blank=True, null=True)
    client = models.CharField(max_length=100, blank=True)
    source_language = models.CharField(max_length=50, blank=True)
    target_language = models.CharField(max_length=50, blank=True)
    duration = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    @property
    def amount(self):
        try:
            if self.duration is None or self.rate is None:
                return Decimal('0')
            return Decimal(str(self.duration)) * Decimal(str(self.rate))
        except (TypeError, ValueError, decimal.InvalidOperation):
            return Decimal('0')
        
        
class Reimbursement(models.Model):
    REIMBURSEMENT_TYPES = [
        ('TRANSPORT', 'Transportation'),
        ('PARKING', 'Parking fees'),
        ('TOLL', 'Toll fees'),
        ('MEAL', 'Meals'),
        ('ACCOMMODATION', 'Accommodation'),
        ('EQUIPMENT', 'Interpretation equipment'),
        ('TRAINING', 'Professional training'),
        ('COMMUNICATION', 'Communication fees'),
        ('PRINTING', 'Document printing'),
        ('OTHER', 'Other reimbursable expense'),
    ]
    
    payroll = models.ForeignKey(PayrollDocument, on_delete=models.CASCADE, related_name='reimbursements')
    date = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=255)
    reimbursement_type = models.CharField(max_length=50, choices=REIMBURSEMENT_TYPES, default='OTHER')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_reimbursement_type_display()}: {self.description} - ${self.amount}"
    
    
class Deduction(models.Model):
    DEDUCTION_TYPES = [
        ('ADVANCE', 'Payment advance'),
        ('EQUIPMENT', 'Provided equipment'),
        ('CANCELLATION', 'Cancellation penalty'),
        ('LATE', 'Late penalty'),
        ('TAX', 'Tax withholding'),
        ('CONTRIBUTION', 'Social contributions'),
        ('ADMIN_FEE', 'Administrative fees'),
        ('ADJUSTMENT', 'Invoice adjustment'),
        ('OTHER', 'Other deduction'),
    ]
    
    payroll = models.ForeignKey(PayrollDocument, on_delete=models.CASCADE, related_name='deductions')
    date = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=255)
    deduction_type = models.CharField(max_length=50, choices=DEDUCTION_TYPES, default='OTHER')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.get_deduction_type_display()}: {self.description} - ${self.amount}"