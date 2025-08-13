from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Department,
    User,
    TeamMember,
    Course,
    CourseTeam,
    Notification
)

# Configuration de base
admin.site.site_header = "OETS Administration"
admin.site.site_title = "OETS Admin Portal"
admin.site.index_title = "Bienvenue sur le portail OETS"

# 1. Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'language', 'display_description')
    search_fields = ('name', 'language')
    list_filter = ('language',)
    
    def display_description(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    display_description.short_description = 'Description'

# 2. User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Professional Info', {'fields': ('role', 'department', 'education_level', 'profession')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_system_user', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'department'),
        }),
    )

admin.site.register(User, CustomUserAdmin)

# 3. TeamMember Admin
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'display_qualifications')
    search_fields = ('full_name', 'email')
    list_per_page = 20
    
    def display_qualifications(self, obj):
        return obj.qualification[:50] + '...' if len(obj.qualification) > 50 else obj.qualification
    display_qualifications.short_description = 'Qualifications'

# 4. Course Admin
class CourseTeamInline(admin.TabularInline):
    model = CourseTeam
    extra = 1
    autocomplete_fields = ['team_member']
    verbose_name = "Team Member Assignment"
    verbose_name_plural = "Team Members Assignments"
    
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'supplier_type', 'created_by', 'created_at', 'submission_deadline')
    list_filter = ('status', 'supplier_type', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CourseTeamInline]  # Gère la relation ManyToMany
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'status', 'supplier_type')
        }),
        ('Content', {
            'fields': ('objectives', 'contents', 'duration', 'links', 'course_summary')
        }),
        ('Administration', {
            'fields': ('expected_income', 'submission_deadline', 'created_by')  # Retirez 'team_members' ici
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# 5. Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'subject', 'is_read', 'sent_at')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('subject', 'message', 'recipient__username')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Marquer comme lu"
    
    actions = [mark_as_read]