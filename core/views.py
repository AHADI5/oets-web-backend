import logging
from django.conf import settings
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from core.models import Course, User, Notification, ParentChildRelationship  
from core.serializers import CustomTokenObtainPairSerializer, CourseSerializer

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
# Set up logging
logger = logging.getLogger(__name__)


# Home page view
@api_view(['GET'])
@permission_classes([AllowAny])
def home_page(request):
    """API documentation home page"""
    return render(request, 'api_documentation.html')

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain endpoint that uses our customized serializer.
    Extends the default TokenObtainPairView to include additional user data in the response.
    """
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom JWT token refresh endpoint.
    Currently maintains default behavior but can be extended if needed.
    """
    pass

class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling all course-related operations including:
    - List/Create/Retrieve/Update/Delete
    - Custom actions like submit
    - Permission-based data filtering
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Custom queryset filtering based on user role:
        - Admins and department heads see all courses
        - Regular users only see courses they created
        
        Returns:
            QuerySet: Filtered list of courses based on user permissions
        """
        user = self.request.user
        
        if user.is_admin or user.is_responsable:
            return Course.objects.all().order_by('-created_at')
        return Course.objects.filter(created_by=user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """
        Perform course creation while letting the serializer handle most logic.
        The serializer already includes permission checks and team member handling.
        """
        try:
            serializer.save()
            logger.info(f"Course created successfully by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            raise
    
    def destroy(self, request, *args, **kwargs):
        """
        Custom course deletion with additional validation:
        - Only draft courses can be deleted
        - Only creator or admin/responsable can delete
        
        Returns:
            Response: Success or error response with appropriate status code
        """
        instance = self.get_object()
        
        # Validate course status
        if instance.status != Course.Status.DRAFT:
            logger.warning(f"User {request.user.id} attempted to delete non-draft course {instance.id}")
            return Response(
                {"error": "Only draft courses can be deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user permissions
        if instance.created_by != request.user and not (
            request.user.is_admin or request.user.is_responsable
        ):
            logger.warning(f"User {request.user.id} attempted to delete course {instance.id} without permission")
            return Response(
                {"error": "You can only delete courses you created"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            self.perform_destroy(instance)
            logger.info(f"Course {instance.id} deleted successfully by user {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting course {instance.id}: {e}")
            return Response(
                {"error": "Failed to delete course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Custom action to submit a draft course for review.
        
        Args:
            request: HTTP request object
            pk: Primary key of the course to submit
            
        Returns:
            Response: Success or error response with appropriate status code
        """
        course = self.get_object()
        
        # Validate course status
        if course.status != Course.Status.DRAFT:
            logger.warning(f"User {request.user.id} attempted to submit non-draft course {course.id}")
            return Response(
                {"error": "Only draft courses can be submitted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user permissions
        if course.created_by != request.user and not (
            request.user.is_admin or request.user.is_responsable
        ):
            logger.warning(f"User {request.user.id} attempted to submit course {course.id} without permission")
            return Response(
                {"error": "You can only submit courses you created"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update course status
        course.status = Course.Status.SUBMITTED
        try:
            course.save()
            logger.info(f"Course {course.id} submitted successfully by user {request.user.id}")
            return Response(
                {
                    "status": "submitted",
                    "new_status": Course.Status.SUBMITTED,
                    "course_id": course.id
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error submitting course {course.id}: {e}")
            return Response(
                {"error": "Failed to submit course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Custom action to publish an approved course.
        """
        course = self.get_object()
        
        # Validate course status - only approved courses can be published
        if course.status != Course.Status.APPROVED:
            logger.warning(f"User {request.user.id} attempted to publish non-approved course {course.id}")
            return Response(
                {"error": "Only approved courses can be published"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user permissions - only specific roles can publish
        user = request.user
        if not (user.is_admin or user.is_responsable):
            logger.warning(f"User {request.user.id} attempted to publish course {course.id} without permission")
            return Response(
                {"error": "Only administrators or department heads can publish courses"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update course status to published
        course.status = Course.Status.PUBLISHED
        try:
            course.save()
            logger.info(f"Course {course.id} published successfully by user {request.user.id}")
            
            # Send notifications
            self._send_publish_notifications(course)
            
            return Response(
                {
                    "status": "published",
                    "new_status": Course.Status.PUBLISHED,
                    "course_id": course.id
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error publishing course {course.id}: {e}")
            return Response(
                {"error": "Failed to publish course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _send_publish_notifications(self, course):
        """
        Send notifications to trainers, parents, and stakeholders when a course is published.
        """
        try:
            # Notify trainers (internal and external)
            self._notify_trainers(course)
            
            # Notify parents/subscribers
            self._notify_subscribers(course)
            
            # Notify stakeholders
            self._notify_stakeholders(course)
            
            logger.info(f"All notifications sent successfully for course {course.id}")
        except Exception as e:
            logger.error(f"Error sending notifications for course {course.id}: {e}")

    def _notify_trainers(self, course):
        """Notify all trainers associated with the course"""
        try:
            # Get internal trainers (users with formateur role)
            internal_trainers = User.objects.filter(role=User.Role.FORMATEUR)
            
            # Get external trainers (team members)
            external_trainers_emails = course.team_members.all().values_list('email', flat=True)
            
            # Combine all recipients
            all_recipients = list(internal_trainers.values_list('email', flat=True)) + list(external_trainers_emails)
            
            # Send email notification
            send_mail(
                subject=f"Course Published: {course.title}",
                message=render_to_string('emails/course_published_trainers.txt', {
                    'course': course,
                    'settings': settings
                }),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=all_recipients,
                fail_silently=False,
            )
            logger.info(f"Notified {len(all_recipients)} trainers for course {course.id}")
        except Exception as e:
            logger.error(f"Error notifying trainers for course {course.id}: {e}")

    def _notify_subscribers(self, course):
        """Notify learners and their parents about the new course"""
        try:
            # Notify all active learners
            learners = User.objects.filter(role=User.Role.LEARNER, is_active=True)
            learner_count = 0
            for learner in learners:
                # Notify the learner
                self._notify_learner(learner, course)
                learner_count += 1
                
                # Notify the learner's parents
                self._notify_learner_parents(learner, course)
            
            # Also notify any parents without specific child relationships
            standalone_parents = User.objects.filter(
                role=User.Role.PARENT, 
                is_active=True,
                children_relationships__isnull=True
            )
            standalone_parent_count = 0
            for parent in standalone_parents:
                self._notify_general_parent(parent, course)
                standalone_parent_count += 1
            
            logger.info(f"Notified {learner_count} learners and {standalone_parent_count} standalone parents for course {course.id}")
        except Exception as e:
            logger.error(f"Error notifying subscribers for course {course.id}: {e}")

    def _notify_learner(self, learner, course):
        """Notify an individual learner"""
        try:
            Notification.objects.create(
                recipient=learner,
                subject=f"New Course Available: {course.title}",
                message=f"We're excited to announce that '{course.title}' is now available for enrollment!",
                course=course
            )
            
            send_mail(
                subject=f"New Course Available: {course.title}",
                message=render_to_string('emails/course_published_learners.txt', {
                    'course': course,
                    'user': learner,
                    'settings': settings
                }),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[learner.email],
                fail_silently=False,
            )
            logger.debug(f"Notified learner {learner.id} about course {course.id}")
        except Exception as e:
            logger.error(f"Error notifying learner {learner.id} about course {course.id}: {e}")

    def _notify_learner_parents(self, learner, course):
        """Notify all parents of a specific learner"""
        try:
            parent_relationships = learner.parent_relationships.select_related('parent').all()
            parent_count = 0
            
            for relationship in parent_relationships:
                parent = relationship.parent
                # Only notify if parent is active
                if not parent.is_active:
                    continue
                    
                Notification.objects.create(
                    recipient=parent,
                    subject=f"New Course for {learner.first_name}: {course.title}",
                    message=f"A new course '{course.title}' is now available that might interest {learner.first_name}!",
                    course=course
                )
                
                send_mail(
                    subject=f"New Learning Opportunity for {learner.first_name}: {course.title}",
                    message=render_to_string('emails/course_published_specific_parent.txt', {
                        'course': course,
                        'parent': parent,
                        'learner': learner,
                        'relationship': relationship,
                        'settings': settings
                    }),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[parent.email],
                    fail_silently=False,
                )
                parent_count += 1
                logger.debug(f"Notified parent {parent.id} about course {course.id} for learner {learner.id}")
            
            if parent_count > 0:
                logger.info(f"Notified {parent_count} parents for learner {learner.id} about course {course.id}")
                
        except Exception as e:
            logger.error(f"Error notifying parents for learner {learner.id} about course {course.id}: {e}")

    def _notify_general_parent(self, parent, course):
        """Notify parents without specific child relationships"""
        try:
            Notification.objects.create(
                recipient=parent,
                subject=f"New Course Available: {course.title}",
                message=f"A new course '{course.title}' is now available for students!",
                course=course
            )
            
            send_mail(
                subject=f"New Learning Opportunity: {course.title}",
                message=render_to_string('emails/course_published_general_parent.txt', {
                    'course': course,
                    'parent': parent,
                    'settings': settings
                }),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[parent.email],
                fail_silently=False,
            )
            logger.debug(f"Notified general parent {parent.id} about course {course.id}")
        except Exception as e:
            logger.error(f"Error notifying general parent {parent.id} about course {course.id}: {e}")

    def _notify_stakeholders(self, course):
        """Notify stakeholders (admins, department heads)"""
        try:
            stakeholders = User.objects.filter(
                role__in=[User.Role.ADMIN, User.Role.RESPONSABLE]
            )
            stakeholder_count = 0
            
            for stakeholder in stakeholders:
                send_mail(
                    subject=f"Course Published: {course.title}",
                    message=render_to_string('emails/course_published_stakeholders.txt', {
                        'course': course,
                        'stakeholder': stakeholder,
                        'settings': settings
                    }),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[stakeholder.email],
                    fail_silently=False,
                )
                stakeholder_count += 1
                logger.debug(f"Notified stakeholder {stakeholder.id} about course {course.id}")
            
            logger.info(f"Notified {stakeholder_count} stakeholders about course {course.id}")
        except Exception as e:
            logger.error(f"Error notifying stakeholders about course {course.id}: {e}")

@api_view(['GET'])
def health_check(request):
    """Endpoint for service health monitoring"""
    logger.debug("Health check endpoint accessed")
    return Response({'status': 'healthy'})

def bad_request(request, exception=None):
    """400 error handler"""
    logger.warning(f"Bad request: {exception}")
    return JsonResponse({'error': 'Bad Request'}, status=400)

def permission_denied(request, exception=None):
    """403 error handler"""
    logger.warning(f"Permission denied: {exception}")
    return JsonResponse({'error': 'Permission Denied'}, status=403)

def page_not_found(request, exception=None):
    """404 error handler"""
    logger.warning(f"Page not found: {exception}")
    return JsonResponse({'error': 'Not Found'}, status=404)

def server_error(request):
    """500 error handler"""
    logger.error("Server error occurred")
    return JsonResponse({'error': 'Server Error'}, status=500)

