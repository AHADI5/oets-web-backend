import os
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.authtoken.models import Token
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings

def validate_file_size(value):
    """
    Validates that uploaded files don't exceed 1MB and have allowed extensions
    Args:
        value: Uploaded file object
    Raises:
        ValidationError: If file fails size or extension checks
    """
    # Size validation (1MB limit)
    if value.size > 1 * 1024 * 1024:
        raise ValidationError(_("File size must be ≤1MB"))
    
    # Extension validation
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.pdf', '.docx', '.txt']:
        raise ValidationError(_("Only PDF, DOCX, or TXT files allowed"))
    
    # Removed virus scan integration to prevent dependency issues
    # You can add this later if needed by installing django-clamd

class Department(models.Model):
    """Represents a language department in the OETS system"""
    name = models.CharField(max_length=100, help_text="Department name (e.g. 'French Department')")
    language = models.CharField(max_length=50, help_text="Primary language taught in this department")
    description = models.TextField(blank=True, help_text="Optional department description")

    def __str__(self):
        return f"{self.name} ({self.language})"

class User(AbstractUser):
    """
    Custom user model with role-based access control
    Extends Django's built-in AbstractUser with OETS-specific fields
    """
    class Role(models.TextChoices):
        """Defines all possible user roles in the system"""
        LEARNER = 'LEARNER', _('Learner')
        FORMATEUR = 'FORMATEUR', _('Formateur') 
        RESPONSABLE = 'RESPONSABLE', _('Responsable')
        SECRETAIRE = 'SECRETAIRE', _('Secrétaire')
        ADMIN = 'ADMIN', _('Administrateur')
        MARKETING = 'MARKETING', _('Marketing')
        PARENT = 'PARENT', _('Parent')
        
    
    # Role check properties - KEEP ONLY THIS SET
    @property
    def is_marketing(self):
        return self.role == self.Role.MARKETING
    
    @property
    def is_parent(self):
        return self.role == self.Role.PARENT
    
    @property
    def is_responsable(self):
        return self.role == self.Role.RESPONSABLE
    
    @property
    def is_learner(self):
        return self.role == self.Role.LEARNER
    
    @property
    def is_formateur(self):
        return self.role == self.Role.FORMATEUR
    
    @property
    def is_secretaire(self):
        return self.role == self.Role.SECRETAIRE
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    # Base Fields
    phone = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Associated department (for staff users)"
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.LEARNER
    )
    
    # Learner-specific fields
    education_level = models.CharField(max_length=100, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    
    # Staff-specific fields
    is_system_user = models.BooleanField(
        default=False,
        help_text="Can access Django admin interface"
    )

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

class ParentChildRelationship(models.Model):
        """Links parents to their children (learners)"""
        parent = models.ForeignKey(
            User, 
            on_delete=models.CASCADE, 
            related_name='children_relationships',
            limit_choices_to={'role': User.Role.PARENT}
        )
        child = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name='parent_relationships', 
            limit_choices_to={'role': User.Role.LEARNER}
        )
        relationship = models.CharField(max_length=100, default="Parent/Guardian")  # e.g., Mother, Father, Guardian
        
        class Meta:
            unique_together = ('parent', 'child')
        
        def __str__(self):
            return f"{self.parent} -> {self.child} ({self.relationship})"
        
class TeamMember(models.Model):
    """External instructors not registered as system users"""
    full_name = models.CharField(max_length=255)
    qualification = models.TextField(help_text="Professional qualifications/certifications")
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

class Course(models.Model):
    """Training course with submission and review workflow"""
    class SupplierType(models.TextChoices):
        INTERNAL = 'INTERNAL', _('Internal Trainer')
        EXTERNAL = 'EXTERNAL', _('External Trainer')
        HOD = 'HOD', _('Head of Department')

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        SUBMITTED = 'SUBMITTED', _('Submitted')
        UNDER_REVIEW = 'UNDER_REVIEW', _('Under Review')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        PUBLISHED = 'PUBLISHED', _('Published') 
        
    # Core Fields
    title = models.CharField(max_length=255)
    description = models.TextField()
    supplier_type = models.CharField(
        max_length=20,
        choices=SupplierType.choices,
        default=SupplierType.INTERNAL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Content Fields
    objectives = models.TextField(help_text="Learning outcomes")
    contents = models.TextField(help_text="Required textbooks/materials")
    duration = models.DurationField(
        default=timedelta(days=1),
        help_text="Format: days hours:minutes:seconds"
    )
    
    # Administrative Fields
    expected_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    links = models.URLField(
        blank=True,
        null=True,
        help_text="External learning resources"
    )
    course_summary = models.FileField(
        upload_to='course_summaries/%Y/%m/',
        validators=[validate_file_size],
        blank=True,
        null=True
    )
    submission_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last submission date for review"
    )

    # Relationships
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='courses_created'
    )
    team_members = models.ManyToManyField(
        TeamMember,
        through='CourseTeam',
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Training Course"
        verbose_name_plural = "Training Courses"

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def clean(self):
        """Business logic validation"""
        if (self.status == self.Status.SUBMITTED and 
            self.submission_deadline and 
            timezone.now() > self.submission_deadline):
            raise ValidationError("Cannot submit after deadline")

    def save(self, *args, **kwargs):
        """Handles status transitions and notifications"""
        is_new = self.pk is None
        old_status = Course.objects.get(pk=self.pk).status if not is_new else None
        
        super().save(*args, **kwargs)
        
        if self.status == self.Status.SUBMITTED and (is_new or old_status != self.Status.SUBMITTED):
            self._send_notifications()

    def _send_notifications(self):
        """Coordinates all notification types"""
        self._notify_submitter()
        self._notify_evaluators()

    def _notify_submitter(self):
        """Send text confirmation to course creator"""
        send_mail(
            subject=f"Course Submitted: {self.title}",
            message=render_to_string('emails/submission_confirm.txt', {
                'course': self,
                'user': self.created_by,
                'settings': settings  # Make sure settings is available in template
            }),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.created_by.email],
            fail_silently=False,
        )

    def _notify_evaluators(self):
        """Send text alerts to evaluators"""
        evaluators = User.objects.filter(
            role__in=[User.Role.RESPONSABLE, User.Role.ADMIN]
        )
        
        for evaluator in evaluators:
            send_mail(
                subject=f"New Course Submission: {self.title}",
                message=render_to_string('emails/evaluator_alert.txt', {
                    'course': self,
                    'evaluator': evaluator,
                    'settings': settings
                }),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[evaluator.email],
                fail_silently=False,
            )

    def check_completeness(self):
        """
        Check if all required fields are completed before submission
        """
        required_fields = ['title', 'description', 'objectives', 'contents', 'duration']
        for field in required_fields:
            value = getattr(self, field)
            if not value or (isinstance(value, str) and value.strip() == ''):
                return False
        return True
    
class CourseTeam(models.Model):
    """Joins Courses with TeamMembers (instructors)"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('course', 'team_member')
    
    def __str__(self):
        return f"{self.team_member} assigned to {self.course}"

class Notification(models.Model):
    """System notifications for users"""
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Notification for {self.recipient}: {self.subject}"

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Automatically generates API tokens for new users"""
    if created:
        Token.objects.create(user=instance)