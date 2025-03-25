from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, strip_tags
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext as _
from django.db import models as django_models
from . import models
from .utils.timezone import (
    MassachusettsTimezoneMixin,
    format_ma_datetime,
    format_ma_date,
    format_ma_time,
    MassachusettsModelFormMixin
)
import pytz
from datetime import datetime
from functools import partial

# Base Admin Mixin for Massachusetts timezone
class MassachusettsBaseAdmin(MassachusettsTimezoneMixin, admin.ModelAdmin):
    def _get_datetime_fields(self, obj):
        """Identifie tous les champs datetime du modèle"""
        return [f.name for f in obj._meta.fields 
                if isinstance(f, (django_models.DateTimeField, django_models.DateField))]

    def get_list_display(self, request):
        """Remplace les champs datetime par leur version formatée"""
        list_display = super().get_list_display(request)
        datetime_fields = self._get_datetime_fields(self.model)
        return [f'format_{name}' if name in datetime_fields else name 
                for name in list_display]

    def get_fieldsets(self, request, obj=None):
        """Ajoute l'indication du fuseau horaire aux fieldsets"""
        fieldsets = super().get_fieldsets(request, obj)
        for fieldset in fieldsets:
            fields = fieldset[1].get('fields', [])
            if any(f in self._get_datetime_fields(self.model) for f in fields):
                description = fieldset[1].get('description', '')
                tz_note = f' (All times are in {self.get_timezone_suffix()})'
                fieldset[1]['description'] = description + tz_note
        return fieldsets

# Email handling mixin
class EmailHandlingMixin:
    def _generate_email_key(self, obj, action_type):
        """Génère une clé unique pour un email"""
        return f"{obj._meta.model_name}_{obj.pk}_{action_type}_{timezone.now().strftime('%Y%m%d')}"

    def _has_email_been_sent(self, key):
        """Vérifie si un email a déjà été envoyé (à implémenter avec votre système de cache)"""
        # Vous pouvez implémenter ceci avec Django cache ou votre propre système
        return False

    def _mark_email_as_sent(self, key):
        """Marque un email comme envoyé (à implémenter avec votre système de cache)"""
        # Vous pouvez implémenter ceci avec Django cache ou votre propre système
        pass

    def send_email_with_tracking(self, subject, context, template_name, recipient_list, request=None):
        """Envoie un email avec suivi et prévention des doublons"""
        email_key = self._generate_email_key(context.get('obj'), subject)
        
        if not self._has_email_been_sent(email_key):
            try:
                # Convertir toutes les dates dans le contexte en heure du Massachusetts
                for key, value in context.items():
                    if isinstance(value, datetime):
                        context[key] = format_ma_datetime(value)

                # Rendre le template avec le contexte
                html_message = render_to_string(
                    template_name,
                    context,
                    request=request
                )

                # Envoyer l'email
                send_mail(
                    subject=subject,
                    message=strip_tags(html_message),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    html_message=html_message,
                    fail_silently=False
                )

                # Marquer l'email comme envoyé
                self._mark_email_as_sent(email_key)
                return True
            except Exception as e:
                print(f"Email sending failed: {str(e)}")
                return False
        return False

# Custom actions
def mark_as_active(modeladmin, request, queryset):
    queryset.update(active=True)
mark_as_active.short_description = "Mark as active"

def mark_as_inactive(modeladmin, request, queryset):
    queryset.update(active=False)
mark_as_inactive.short_description = "Mark as inactive"

def reset_password(modeladmin, request, queryset):
    for user in queryset:
        # Password reset logic
        pass
reset_password.short_description = "Reset password"

# Inline Models
class InterpreterLanguageInline(admin.TabularInline):
    model = models.InterpreterLanguage
    extra = 1
    classes = ['collapse']
    fields = ('language', 'proficiency', 'is_primary', 'certified', 'certification_details')

class AssignmentInline(admin.TabularInline):
    model = models.Assignment
    extra = 0
    readonly_fields = ['format_created_at', 'format_updated_at']
    classes = ['collapse']

    def format_created_at(self, obj):
        return format_ma_datetime(obj.created_at)
    format_created_at.short_description = 'Created At (EST/EDT)'

    def format_updated_at(self, obj):
        return format_ma_datetime(obj.updated_at)
    format_updated_at.short_description = 'Updated At (EST/EDT)'

@admin.register(models.User)
class CustomUserAdmin(UserAdmin, MassachusettsTimezoneMixin):
    list_display = ('username', 'email', 'role', 'is_active', 'format_last_login', 
                   'format_date_joined', 'registration_complete')
    list_filter = ('role', 'is_active', 'groups', 'registration_complete')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = [reset_password, mark_as_active, mark_as_inactive]

    def format_last_login(self, obj):
        return format_ma_datetime(obj.last_login)
    format_last_login.short_description = 'Last Login (EST/EDT)'

    def format_date_joined(self, obj):
        return format_ma_datetime(obj.date_joined)
    format_date_joined.short_description = 'Date Joined (EST/EDT)'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Information'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Role and Status'), {'fields': ('role', 'is_active', 'registration_complete')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined'),
            'description': 'All times are shown in Massachusetts time (EST/EDT)'
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        if not is_superuser:
            form.base_fields['role'].disabled = True
        return form

@admin.register(models.Assignment)
class AssignmentAdmin(MassachusettsBaseAdmin, EmailHandlingMixin):
    list_display = ('id', 'get_client', 'get_interpreter', 'format_start_time', 'status')
    list_filter = ('status', 'service_type', 'start_time')
    search_fields = ('client__company_name', 'interpreter__user__first_name', 
                    'interpreter__user__last_name')
    raw_id_fields = ('quote', 'interpreter', 'client')
    readonly_fields = ('format_created_at', 'format_updated_at', 'format_completed_at')

    def format_start_time(self, obj):
        return format_ma_datetime(obj.start_time)
    format_start_time.short_description = 'Start Time (EST/EDT)'
    format_start_time.admin_order_field = 'start_time'

    def format_created_at(self, obj):
        return format_ma_datetime(obj.created_at)
    format_created_at.short_description = 'Created At (EST/EDT)'

    def format_updated_at(self, obj):
        return format_ma_datetime(obj.updated_at)
    format_updated_at.short_description = 'Updated At (EST/EDT)'

    def format_completed_at(self, obj):
        return format_ma_datetime(obj.completed_at)
    format_completed_at.short_description = 'Completed At (EST/EDT)'

    fieldsets = (
        ('Assignment Information', {
            'fields': (('quote', 'service_type'), ('interpreter', 'client'))
        }),
        ('Language Details', {
            'fields': ('source_language', 'target_language')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time'),
            'description': 'All times are in Massachusetts time (EST/EDT)'
        }),
        ('Location', {
            'fields': ('location', ('city', 'state', 'zip_code'))
        }),
        ('Financial Information', {
            'fields': ('interpreter_rate', 'minimum_hours', 'total_interpreter_payment'),
            'classes': ('collapse',)
        }),
        ('Status and Notes', {
            'fields': ('status', 'notes', 'special_requirements')
        }),
        ('System Information', {
            'fields': ('format_created_at', 'format_updated_at', 'format_completed_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        # Convertir les heures en UTC avant la sauvegarde
        if obj.start_time:
            obj.start_time = self.from_ma_time(obj.start_time)
        if obj.end_time:
            obj.end_time = self.from_ma_time(obj.end_time)

        # Vérifier si un email doit être envoyé
        should_send = False
        if not change:  # Nouvelle création
            should_send = (obj.status == models.Assignment.Status.PENDING and 
                         obj.interpreter is not None)
        else:  # Modification
            try:
                old_obj = self.model.objects.get(pk=obj.pk)
                should_send = (old_obj.status != obj.status and 
                             obj.status == models.Assignment.Status.PENDING and 
                             obj.interpreter is not None)
            except self.model.DoesNotExist:
                pass

        # Sauvegarder le modèle
        super().save_model(request, obj, form, change)

        # Envoyer l'email si nécessaire
        if should_send and obj.interpreter:
            context = {
                'obj': obj,  # Pour la génération de la clé d'email
                'interpreter_name': f"{obj.interpreter.user.first_name} {obj.interpreter.user.last_name}",
                'assignment_id': obj.id,
                'start_time': obj.start_time,
                'end_time': obj.end_time,
                'location': obj.location,
                'city': obj.city,
                'state': obj.state,
                'client_name': obj.client.company_name,
                'service_type': obj.service_type.name,
                'source_language': obj.source_language.name,
                'target_language': obj.target_language.name,
                'interpreter_rate': obj.interpreter_rate,
                'special_requirements': obj.special_requirements or "No special requirements"
            }

            email_sent = self.send_email_with_tracking(
                subject=_('New Assignment to Confirm - Action Required'),
                context=context,
                template_name='emails/new_assignment_notification.html',
                recipient_list=[obj.interpreter.user.email],
                request=request
            )

            if email_sent:
                self.message_user(
                    request,
                    f"Assignment saved and notification email sent to interpreter "
                    f"(times shown in {self.get_timezone_suffix()})",
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    "Assignment saved but there was an issue sending the notification email",
                    messages.WARNING
                )

@admin.register(models.Quote)
class QuoteAdmin(MassachusettsBaseAdmin):
    list_display = ('reference_number', 'get_client', 'amount', 'status', 'format_created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reference_number', 'quote_request__client__company_name')
    readonly_fields = ('format_created_at', 'format_updated_at')
    raw_id_fields = ('quote_request', 'created_by')

    def format_created_at(self, obj):
        return format_ma_datetime(obj.created_at)
    format_created_at.short_description = 'Created At (EST/EDT)'

    def format_updated_at(self, obj):
        return format_ma_datetime(obj.updated_at)
    format_updated_at.short_description = 'Updated At (EST/EDT)'

    fieldsets = (
        ('Quote Information', {
            'fields': ('quote_request', 'reference_number', 'status')
        }),
        ('Financial Details', {
            'fields': ('amount', 'tax_amount', 'valid_until')
        }),
        ('Additional Information', {
            'fields': ('terms', 'created_by')
        }),
        ('System Information', {
            'fields': ('format_created_at', 'format_updated_at'),
            'classes': ('collapse',),
            'description': 'All times are in Massachusetts time (EST/EDT)'
        })
    )

    def get_client(self, obj):
        return obj.quote_request.client.company_name
    get_client.short_description = 'Client'

@admin.register(models.Payment)
class PaymentAdmin(MassachusettsBaseAdmin):
    list_display = ('transaction_id', 'payment_type', 'amount', 'status', 'format_payment_date')
    list_filter = ('status', 'payment_type', 'payment_date')
    search_fields = ('transaction_id', 'assignment__client__company_name')
    readonly_fields = ('format_payment_date', 'format_last_updated')

    def format_payment_date(self, obj):
        return format_ma_datetime(obj.payment_date)
    format_payment_date.short_description = 'Payment Date (EST/EDT)'

    def format_last_updated(self, obj):
        return format_ma_datetime(obj.last_updated)
    format_last_updated.short_description = 'Last Updated (EST/EDT)'

    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_type', 'amount', 'payment_method')
        }),
        ('Related Records', {
            'fields': ('quote', 'assignment')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'status', 'notes')
        }),
        ('System Information', {
            'fields': ('payment_date', 'last_updated'),
            'classes': ('collapse',),
            'description': 'All times are in Massachusetts time (EST/EDT)'
        })
    )
    
@admin.register(models.Language)
class LanguageAdmin(MassachusettsBaseAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('name',)
    actions = [mark_as_active, mark_as_inactive]

@admin.register(models.Client)
class ClientAdmin(MassachusettsBaseAdmin):
    list_display = ('get_full_name', 'company_name', 'city', 'state', 'active')
    list_filter = ('active', 'state', 'preferred_language')
    search_fields = ('company_name', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    readonly_fields = ('credit_limit',)

    fieldsets = (
        ('Basic Information', {
            'fields': (('user', 'active'), 'company_name', 'preferred_language')
        }),
        ('Primary Address', {
            'fields': ('address', ('city', 'state', 'zip_code'))
        }),
        ('Billing Information', {
            'fields': ('billing_address', ('billing_city', 'billing_state', 'billing_zip_code'),
                      'tax_id', 'credit_limit'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Full Name'

@admin.register(models.Interpreter)
class InterpreterAdmin(MassachusettsBaseAdmin):
    list_display = (
        'get_full_name',
        'get_languages',
        'city', 
        'state',
        'active',
        'w9_on_file',
        'format_background_check_date',
        'background_check_status',
        'hourly_rate'
    )
    list_filter = (
        'active',
        'state',
        'w9_on_file',
        'background_check_status',
        'languages'
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'city',
        'state',
        'zip_code'
    )
    inlines = [InterpreterLanguageInline]

    def format_background_check_date(self, obj):
        return format_ma_date(obj.background_check_date)
    format_background_check_date.short_description = 'Background Check Date'

    fieldsets = (
        ('Status', {
            'fields': (
                ('user', 'active'),
            )
        }),
        ('Profile Information', {
            'fields': (
                'profile_image',
                'bio'
            )
        }),
        ('Contact Information', {
            'fields': (
                'address',
                ('city', 'state', 'zip_code'),
                'radius_of_service'
            )
        }),
        ('Professional Information', {
            'fields': (
                'hourly_rate',
                'certifications',
                'specialties',
                'availability'
            )
        }),
        ('Compliance', {
            'fields': (
                ('background_check_date', 'background_check_status'),
                'w9_on_file'
            ),
            'classes': ('collapse',)
        }),
        ('Banking Information (ACH)', {
            'fields': (
                'bank_name',
                'account_holder_name',
                'routing_number',
                'account_number',
                'account_type'
            ),
            'classes': ('collapse',),
            'description': 'Secure banking information for ACH payments.'
        })
    )

@admin.register(models.QuoteRequest)
class QuoteRequestAdmin(MassachusettsBaseAdmin):
    list_display = ('id', 'client', 'service_type', 'format_requested_date', 'status', 'format_created_at')
    list_filter = ('status', 'service_type', 'created_at')
    search_fields = ('client__company_name', 'location')
    readonly_fields = ('format_created_at', 'format_updated_at')

    def format_requested_date(self, obj):
        return format_ma_datetime(obj.requested_date)
    format_requested_date.short_description = 'Requested Date (EST/EDT)'

    def format_created_at(self, obj):
        return format_ma_datetime(obj.created_at)
    format_created_at.short_description = 'Created At (EST/EDT)'

    fieldsets = (
        ('Client Information', {
            'fields': ('client', 'service_type')
        }),
        ('Service Details', {
            'fields': ('requested_date', 'duration', ('source_language', 'target_language'))
        }),
        ('Location', {
            'fields': ('location', ('city', 'state', 'zip_code'))
        }),
        ('Additional Information', {
            'fields': ('special_requirements', 'status')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'All times are in Massachusetts time (EST/EDT)'
        })
    )

@admin.register(models.Notification)
class NotificationAdmin(MassachusettsBaseAdmin):
    list_display = ('recipient', 'type', 'title', 'read', 'format_created_at')
    list_filter = ('type', 'read', 'created_at')
    search_fields = ('recipient__email', 'title', 'content')
    readonly_fields = ('format_created_at',)

    def format_created_at(self, obj):
        return format_ma_datetime(obj.created_at)
    format_created_at.short_description = 'Created At (EST/EDT)'

@admin.register(models.ContactMessage)
class ContactMessageAdmin(MassachusettsBaseAdmin):
    list_display = ('subject', 'name', 'email', 'format_created_at', 'processed')
    list_filter = ('processed', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('format_created_at', 'format_processed_at')

    def format_created_at(self, obj):
        return format_ma_datetime(obj.created_at)
    format_created_at.short_description = 'Created At (EST/EDT)'

    def format_processed_at(self, obj):
        return format_ma_datetime(obj.processed_at)
    format_processed_at.short_description = 'Processed At (EST/EDT)'

    actions = ['mark_as_processed']

    def mark_as_processed(self, request, queryset):
        queryset.update(
            processed=True,
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(
            request,
            f"{queryset.count()} message(s) marked as processed."
        )
    mark_as_processed.short_description = "Mark selected messages as processed"

@admin.register(models.AuditLog)
class AuditLogAdmin(MassachusettsBaseAdmin):
    list_display = ('format_timestamp', 'user', 'action', 'model_name', 'object_id')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__email', 'action', 'changes')
    readonly_fields = ('format_timestamp', 'user', 'action', 'model_name', 
                      'object_id', 'changes', 'ip_address')

    def format_timestamp(self, obj):
        return format_ma_datetime(obj.timestamp)
    format_timestamp.short_description = 'Timestamp (EST/EDT)'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(models.PublicQuoteRequest)
class PublicQuoteRequestAdmin(MassachusettsBaseAdmin):
    list_display = (
        'full_name', 
        'company_name', 
        'get_languages', 
        'service_type', 
        'format_requested_date', 
        'format_created_at', 
        'processed'
    )
    list_filter = (
        'processed',
        'service_type',
        'source_language',
        'target_language',
        'state',
        'created_at'
    )
    search_fields = (
        'full_name',
        'email',
        'phone',
        'company_name',
        'location',
        'city'
    )

    def format_requested_date(self, obj):
        return format_ma_datetime(obj.requested_date)
    format_requested_date.short_description = 'Requested Date (EST/EDT)'

    def format_created_at(self, obj):
        return format_ma_datetime(obj.created_at)
    format_created_at.short_description = 'Created At (EST/EDT)'

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now()
        ma_time = self.to_ma_time(timestamp)
        response['Content-Disposition'] = (
            f'attachment; filename=quote_requests_{ma_time.strftime("%Y%m%d")}.csv'
        )
        writer = csv.writer(response)

        # Write header with timezone indication
        writer.writerow([f"{field} (EST/EDT)" if isinstance(meta.get_field(field),
            (django_models.DateTimeField, django_models.DateField)) else field
            for field in field_names])
        
        # Write data
        for obj in queryset:
            row = []
            for field in field_names:
                value = getattr(obj, field)
                if isinstance(value, datetime):
                    value = format_ma_datetime(value)
                row.append(str(value))
            writer.writerow(row)

        return response
    export_as_csv.short_description = "Export selected requests to CSV"

# Admin site configuration with timezone indication
admin.site.site_header = "DBD I&T Administration (All times EST/EDT)"
admin.site.site_title = "DBD I&T Admin Portal"
admin.site.index_title = "Welcome to DBD I&T Administration"