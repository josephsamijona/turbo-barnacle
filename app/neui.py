# views.py

from django.views.generic import TemplateView
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.core.signing import Signer, BadSignature
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.utils.html import strip_tags
from datetime import datetime, timedelta
import pytz
import icalendar
import uuid

# Pour manipuler la pièce jointe ICS
import smtplib
from email.mime.base import MIMEBase
from email import encoders
from email.utils import make_msgid
from icalendar import Calendar, Event, vCalAddress

from app.models import Assignment, AuditLog, User

# Définir le timezone de Boston
BOSTON_TZ = pytz.timezone('America/New_York')


class AssignmentResponseBaseMixin:
    """Base mixin for handling assignment responses (accept/decline)."""
    
    def verify_token(self, token, action):
        """
        Vérifie la validité du token signé (assignment_id, action, timestamp).
        Retourne l'ID de l'Assignment si valide, sinon None.
        """
        signer = Signer()
        try:
            data = signer.unsign(token)
            assignment_id, token_action, timestamp, _ = data.split(':', 3)
            
            # Vérifie que l'action correspond
            if token_action != action:
                return None

            # Vérifie l'expiration (24h) en timezone de Boston
            token_time = datetime.fromtimestamp(float(timestamp))
            token_time = BOSTON_TZ.localize(token_time)
            if timezone.now().astimezone(BOSTON_TZ) - token_time > timedelta(hours=24):
                return None
            
            return int(assignment_id)
        
        except (BadSignature, ValueError):
            return None

    def handle_expired_token(self, request):
        """
        Rend une page indiquant que le lien a expiré ou n'est plus valide.
        """
        return render(request, 'pages/token_expired.html', {
            'title': _('Link Expired'),
            'message': _('This link has expired or is no longer valid.'),
            'login_url': reverse('dbdint:login')
        })

    def handle_already_processed(self, request):
        """
        Rend une page indiquant que l'Assignment a déjà été traité.
        """
        return render(request, 'pages/already_processed.html', {
            'title': _('Already Processed'),
            'message': _('This assignment has already been processed.'),
            'login_url': reverse('dbdint:login')
        })

    def log_action(self, assignment, action, user, changes=None):
        """
        Log l'action réalisée sur l'Assignment dans l'AuditLog.
        """
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name='Assignment',
            object_id=str(assignment.id),
            changes=changes or {}
        )

    def send_confirmation_to_interpreter(self, assignment):
        """
        Envoie un email unique (avec un Message-ID spécifique)
        et inclut une pièce jointe ICS (invitation calendrier).
        Cela permet, chez la plupart des clients, d'avoir un bouton
        'Ajouter au calendrier' ou 'Accepter / Refuser'.
        """
        interpreter = assignment.interpreter
        client_name = assignment.client_name or "Anonymous Client"
        
        # Identifiant unique pour éviter le regroupement
        unique_id = uuid.uuid4().hex[:8]
        
        # Contexte pour le template HTML
        context = {
            'interpreter_name': interpreter.user.get_full_name(),
            'assignment': assignment,
            'client_name': client_name,
            'client_phone':assignment.client_phone,
            'start_time': assignment.start_time.astimezone(BOSTON_TZ),
            'end_time': assignment.end_time.astimezone(BOSTON_TZ),
            'location': f"{assignment.location}, {assignment.city}, {assignment.state}",
            'service_type': assignment.service_type.name,
            'languages': f"{assignment.source_language.name} → {assignment.target_language.name}",
            'rate': assignment.interpreter_rate,
            'special_requirements': assignment.special_requirements or 'None',
            'reference_id': unique_id
        }
        
        # Rendu HTML
        html_message = render_to_string('notifmail/interpreter_assignment_confirmation.html', context)
        text_message = strip_tags(html_message)
        
        # Création d'un événement iCalendar
        cal = Calendar()
        cal.add('PRODID', '-//DBD I&TAssignment System//EN')
        cal.add('VERSION', '2.0')
        cal.add('METHOD', 'REQUEST')  # Indique qu'il s'agit d'une invitation

        event = Event()
        # Ajouter l'identifiant unique dans le résumé
        event.add('SUMMARY', f"Interpretation Assignment - {assignment.service_type.name} (Ref:{unique_id})")
        
        start_time = assignment.start_time.astimezone(BOSTON_TZ)
        end_time = assignment.end_time.astimezone(BOSTON_TZ)
        
        event.add('DTSTART', start_time)
        event.add('DTEND', end_time)
        event.add('DTSTAMP', timezone.now().astimezone(pytz.UTC))
        event.add('CREATED', timezone.now().astimezone(pytz.UTC))
        event.add('LOCATION', f"{assignment.location}, {assignment.city}, {assignment.state}")
        
        description = (
            f"Client: {client_name}\n"
            f"Service: {assignment.service_type.name}\n"
            f"Languages: {assignment.source_language.name} → {assignment.target_language.name}\n"
            f"Location: {assignment.location}, {assignment.city}, {assignment.state} {assignment.zip_code}\n\n"
            f"Special Requirements: {assignment.special_requirements or 'None'}\n\n"
            f"Rate: ${assignment.interpreter_rate}/hour\n\n"
            f"Reference: {unique_id}\n"
        )
        event.add('DESCRIPTION', description)
        
        # UID unique avec l'identifiant spécifique à cet email
        event.add('UID', f"assignment-{assignment.id}-{unique_id}@dbdint.com")

        # ORGANIZER (expéditeur)
        organizer_email = settings.DEFAULT_FROM_EMAIL
        organizer = vCalAddress(f"MAILTO:{organizer_email}")
        organizer.params['CN'] = "DBD I&T System"
        event['ORGANIZER'] = organizer

        # ATTENDEE (interprète), RSVP=TRUE pour Outlook/Apple Mail
        attendee = vCalAddress(f"MAILTO:{interpreter.user.email}")
        attendee.params['CN'] = interpreter.user.get_full_name()
        attendee.params['RSVP'] = 'TRUE'
        event.add('ATTENDEE', attendee)
        
        cal.add_component(event)
        ics_data = cal.to_ical()

        # Sujet avec ID unique pour éviter le regroupement
        subject = f'Assignment Confirmation #{assignment.id} - Calendar Invitation [{unique_id}]'
        
        # Message-ID unique pour cet email
        unique_message_id = make_msgid(domain="dbdint.co")

        # En-têtes supplémentaires pour éviter le regroupement
        headers = {
            'Message-ID': unique_message_id,
            'X-Entity-Ref-ID': f"{unique_id}@dbdint.co",
            'X-No-Threading': 'true',
            'Thread-Topic': f"DBD Assignment {unique_id}",
            'Thread-Index': unique_id
        }

        # Construction de l'email multi-part
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=organizer_email,
            to=[interpreter.user.email],
            headers=headers,
        )
        # Partie HTML
        email.attach_alternative(html_message, "text/html")

        # Pièce jointe ICS avec nom unique
        ical_part = MIMEBase('text', 'calendar', method='REQUEST', name=f'invite-{unique_id}.ics')
        ical_part.set_payload(ics_data)
        encoders.encode_base64(ical_part)
        ical_part.add_header('Content-Disposition', f'attachment; filename="invite-{unique_id}.ics"')
        ical_part.add_header('Content-class', 'urn:content-classes:calendarmessage')
        email.attach(ical_part)

        # Envoi
        email.send(fail_silently=False)

    def send_decline_confirmation(self, assignment, interpreter):
        """
        Envoie un email de confirmation de refus à l'interprète (sans ICS).
        """
        client_name = assignment.client_name or "Anonymous Client"
        
        # Identifiant unique pour éviter le regroupement
        unique_id = uuid.uuid4().hex[:8]
        
        context = {
            'interpreter_name': interpreter.user.get_full_name(),
            'assignment': assignment,
            'client_name': client_name,
            'client_phone': assignment.client_phone,
            'start_time': assignment.start_time.astimezone(BOSTON_TZ),
            'reference_id': unique_id
        }
        
        html_message = render_to_string(
            'notifmail/interprter_assignment_decline_confirmation.html',
            context
        )
        text_message = strip_tags(html_message)
        
        # Sujet avec ID unique
        subject = f'Assignment Declined - Confirmation [{unique_id}]'
        
        # Message-ID unique pour cet email
        unique_message_id = make_msgid(domain="dbdint.co")
        
        # En-têtes pour éviter le regroupement
        headers = {
            'Message-ID': unique_message_id,
            'X-Entity-Ref-ID': f"{unique_id}@dbdint.co",
            'X-No-Threading': 'true',
            'Thread-Topic': f"DBD Assignment Decline {unique_id}",
            'Thread-Index': unique_id
        }
        
        # Construction de l'email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[interpreter.user.email],
            headers=headers,
        )
        email.attach_alternative(html_message, "text/html")
        
        # Envoi
        email.send(fail_silently=False)

    def notify_admin(self, assignment, action, interpreter):
        """
        Informe les administrateurs (ceux ayant role=ADMIN en BD) d'une action
        (accept/decline) sur un Assignment.
        """
        client_name = assignment.client_name or "Anonymous Client"
        
        # Identifiant unique pour éviter le regroupement
        unique_id = uuid.uuid4().hex[:8]
        
        context = {
            'interpreter_name': interpreter.user.get_full_name(),
            'assignment': assignment,
            'client_name': client_name,
            'action': action,
            'admin_url': reverse('admin:app_assignment_change', args=[assignment.id]),
            'reference_id': unique_id
        }
        
        template = 'notifmail/admin_assignment_response.html'
        html_message = render_to_string(template, context)
        text_message = strip_tags(html_message)
        
        # Récupère tous les utilisateurs avec role=ADMIN
        admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
        admin_emails = [admin_user.email for admin_user in admin_users if admin_user.email]

        if not admin_emails:
            return  # Aucun admin, on quitte silencieusement ou on log
        
        # Sujet avec ID unique
        subject = f'Assignment {action} by {interpreter.user.get_full_name()} [{unique_id}]'
        
        # Message-ID unique pour cet email
        unique_message_id = make_msgid(domain="dbdint.co")
        
        # En-têtes pour éviter le regroupement
        headers = {
            'Message-ID': unique_message_id,
            'X-Entity-Ref-ID': f"{unique_id}@dbdint.co",
            'X-No-Threading': 'true',
            'Thread-Topic': f"DBD Admin Notification {unique_id}",
            'Thread-Index': unique_id
        }
        
        # Construction de l'email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
            headers=headers,
        )
        email.attach_alternative(html_message, "text/html")
        
        # Envoi
        email.send(fail_silently=False)


class AssignmentAcceptView(AssignmentResponseBaseMixin, TemplateView):
    """
    Vue appelée lorsqu'un interprète clique sur le lien d'acceptation.
    Vérifie le token, met à jour le statut de l'Assignment et envoie
    la notification + invitation calendrier.
    """
    template_name = 'pages/accept_success.html'
    
    def get(self, request, assignment_token):
        assignment_id = self.verify_token(assignment_token, 'accept')
        
        if not assignment_id:
            return self.handle_expired_token(request)
        
        try:
            assignment = Assignment.objects.get(id=assignment_id)
            
            if assignment.status != Assignment.Status.PENDING:
                return self.handle_already_processed(request)

            # Update assignment status
            old_status = assignment.status
            assignment.status = Assignment.Status.CONFIRMED
            assignment.save()

            # Notifications
            self.send_confirmation_to_interpreter(assignment)
            self.notify_admin(assignment, 'accepted', assignment.interpreter)

            # Log
            self.log_action(
                assignment=assignment,
                action='ASSIGNMENT_ACCEPTED',
                user=assignment.interpreter.user,
                changes={
                    'old_status': old_status,
                    'new_status': Assignment.Status.CONFIRMED
                }
            )

            # Contexte pour la page de confirmation
            client_name = assignment.client_name or "Anonymous Client"
            
            context = {
                'title': _('Assignment Accepted'),
                'assignment': assignment,
                'interpreter_name': assignment.interpreter.user.get_full_name(),
                'client_name': client_name,
                'start_time': assignment.start_time.astimezone(BOSTON_TZ),
                'end_time': assignment.end_time.astimezone(BOSTON_TZ),
                'location': f"{assignment.location}, {assignment.city}, {assignment.state}",
                'login_url': reverse('dbdint:login')
            }
            
            return render(request, self.template_name, context)
        
        except Assignment.DoesNotExist:
            return render(request, 'pages/not_found.html', {
                'title': _('Assignment Not Found'),
                'message': _('The requested assignment could not be found.'),
                'login_url': reverse('dbdint:login')
            })


class AssignmentDeclineView(AssignmentResponseBaseMixin, TemplateView):
    """
    Vue appelée lorsqu'un interprète clique sur le lien de refus.
    Vérifie le token, met à jour le statut de l'Assignment et notifie
    l'interprète et l'admin.
    """
    template_name = 'pages/decline_success.html'
    
    def get(self, request, assignment_token):
        assignment_id = self.verify_token(assignment_token, 'decline')
        
        if not assignment_id:
            return self.handle_expired_token(request)
        
        try:
            assignment = Assignment.objects.get(id=assignment_id)
            
            if assignment.status != Assignment.Status.PENDING:
                return self.handle_already_processed(request)

            interpreter = assignment.interpreter
            old_status = assignment.status
            
            # Update assignment status + remove interpreter
            assignment.status = Assignment.Status.CANCELLED
            assignment.interpreter = None
            assignment.save()

            # Notifications
            self.send_decline_confirmation(assignment, interpreter)
            self.notify_admin(assignment, 'declined', interpreter)

            # Log
            self.log_action(
                assignment=assignment,
                action='ASSIGNMENT_DECLINED',
                user=interpreter.user,
                changes={
                    'old_status': old_status,
                    'new_status': Assignment.Status.CANCELLED,
                    'reason': 'declined_by_interpreter'
                }
            )

            # Contexte pour la page de confirmation
            client_name = assignment.client_name or "Anonymous Client"
            
            context = {
                'title': _('Assignment Declined'),
                'interpreter_name': interpreter.user.get_full_name(),
                'client_name': client_name,
                'start_time': assignment.start_time.astimezone(BOSTON_TZ),
                'login_url': reverse('dbdint:login')
            }
            
            return render(request, self.template_name, context)
        
        except Assignment.DoesNotExist:
            return render(request, 'pages/not_found.html', {
                'title': _('Assignment Not Found'),
                'message': _('The requested assignment could not be found.'),
                'login_url': reverse('dbdint:login')
            })