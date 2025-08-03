# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model for learners"""
    phone = models.CharField(max_length=20, blank=True)
    education_level = models.CharField(max_length=100, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    registration_date = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

class Department(models.Model):
    """Language department model"""
    name = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Staff(models.Model):
    """Staff member model"""
    class Role(models.TextChoices):
        MANAGER = 'MANAGER', _('Manager')
        SECRETARY = 'SECRETARY', _('Secretary')
        TEACHER = 'TEACHER', _('Teacher')
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    is_system_user = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

class Course(models.Model):
    """Course model"""
    class Format(models.TextChoices):
        IN_PERSON = 'IN_PERSON', _('In person')
        ONLINE = 'ONLINE', _('Online')
    
    class Status(models.TextChoices):
        OPEN = 'OPEN', _('Open')
        PENDING = 'PENDING', _('Pending')
        ARCHIVED = 'ARCHIVED', _('Archived')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    duration = models.PositiveIntegerField(help_text=_("Duration in weeks"))
    format = models.CharField(max_length=20, choices=Format.choices)
    location = models.CharField(max_length=150, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(Staff, related_name='courses', limit_choices_to={'role': Staff.Role.TEACHER})
    
    def __str__(self):
        return self.title

class Enrollment(models.Model):
    """Course enrollment model"""
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)
    motivation = models.TextField(blank=True)
    cv_file = models.FileField(upload_to='enrollments/cvs/', blank=True, null=True)
    motivation_file = models.FileField(upload_to='enrollments/motivations/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    class Meta:
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.course.title}"

class CustomRequest(models.Model):
    """Custom training request model"""
    class Type(models.TextChoices):
        INDIVIDUAL = 'INDIVIDUAL', _('Individual')
        GROUP = 'GROUP', _('Group')
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSED = 'PROCESSED', _('Processed')
        REJECTED = 'REJECTED', _('Rejected')
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    request_type = models.CharField(max_length=20, choices=Type.choices)
    organization_name = models.CharField(max_length=150, blank=True)
    needs_description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    request_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Request #{self.id} - {self.get_request_type_display()}"

class Page(models.Model):
    """CMS Page model"""
    title = models.CharField(max_length=150)
    html_content = models.TextField()
    slug = models.SlugField(max_length=150, unique=True)
    is_visible = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class News(models.Model):
    """News/Announcement model"""
    title = models.CharField(max_length=150)
    content = models.TextField()
    publication_date = models.DateField(auto_now_add=True)
    image = models.ImageField(upload_to='news/images/', blank=True, null=True)
    author = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.title

class Testimonial(models.Model):
    """Student testimonial model"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    publication_date = models.DateField(auto_now_add=True)
    is_visible = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Testimonial by {self.user.get_full_name()}"

class Media(models.Model):
    """Media file model"""
    class MediaType(models.TextChoices):
        PDF = 'PDF', _('PDF')
        IMAGE = 'IMAGE', _('Image')
        VIDEO = 'VIDEO', _('Video')
    
    file_name = models.CharField(max_length=255)
    media_type = models.CharField(max_length=20, choices=MediaType.choices)
    file_url = models.URLField()
    uploaded_by = models.ForeignKey(Staff, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file_name