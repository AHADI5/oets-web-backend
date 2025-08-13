from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Course
from core.serializers import CustomTokenObtainPairSerializer, CourseSerializer


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
        serializer.save()
    
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
            return Response(
                {"error": "Only draft courses can be deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user permissions
        if instance.created_by != request.user and not (
            request.user.is_admin or request.user.is_responsable
        ):
            return Response(
                {"error": "You can only delete courses you created"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
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
            return Response(
                {"error": "Only draft courses can be submitted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user permissions
        if course.created_by != request.user and not (
            request.user.is_admin or request.user.is_responsable
        ):
            return Response(
                {"error": "You can only submit courses you created"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update course status
        course.status = Course.Status.SUBMITTED
        course.save()
        
        return Response(
            {
                "status": "submitted",
                "new_status": Course.Status.SUBMITTED,
                "course_id": course.id
            },
            status=status.HTTP_200_OK
        )
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health_check(request):
    """Endpoint for service health monitoring"""
    return Response({'status': 'healthy'})

def bad_request(request, exception=None):
    """400 error handler"""
    return JsonResponse({'error': 'Bad Request'}, status=400)

def permission_denied(request, exception=None):
    """403 error handler"""
    return JsonResponse({'error': 'Permission Denied'}, status=403)

def page_not_found(request, exception=None):
    """404 error handler"""
    return JsonResponse({'error': 'Not Found'}, status=404)

def server_error(request):
    """500 error handler"""
    return JsonResponse({'error': 'Server Error'}, status=500)