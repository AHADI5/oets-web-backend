from datetime import timezone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from core.models import Course, TeamMember, CourseTeam, User  


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that adds additional user claims to the token
    and includes user details in the authentication response.
    
    Inherits from TokenObtainPairSerializer to maintain default JWT behavior
    while extending it with custom user data.
    """
    
    @classmethod
    def get_token(cls, user):
        """
        Create the JWT token with custom claims (payload data).
        
        Args:
            user: The user instance for whom the token is being created
            
        Returns:
            Token: The JWT token with custom claims
        """
        token = super().get_token(user)

        # Add custom claims to token payload
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['role'] = user.role
        token['department'] = user.department.name if user.department else None
        token['is_system_user'] = user.is_system_user

        return token

    def validate(self, attrs):
        """
        Validate user credentials and add user details to the response.
        
        Args:
            attrs: Dictionary containing username and password
            
        Returns:
            dict: Authentication response with token and user details
        """
        # Perform default validation to get the token
        data = super().validate(attrs)
        
        # Structure user data for the response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'department': self.user.department.name if self.user.department else None,
            'phone': self.user.phone,
            'is_system_user': self.user.is_system_user
        }
        
        return data


class TeamMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for TeamMember model.
    Handles serialization/deserialization of team member data.
    """
    
    class Meta:
        model = TeamMember
        fields = ['id', 'full_name', 'qualification', 'email']
        read_only_fields = ['id']  # Prevent ID modification after creation


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model with nested team members.
    Handles complex course operations including creation, updates, and team management.
    """
    
    team_members = TeamMemberSerializer(many=True, required=False)
    created_by = serializers.StringRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'supplier_type', 'duration',
            'objectives', 'expected_income', 'contents', 'links',
            'course_summary', 'status', 'created_by', 'created_at',
            'updated_at', 'team_members', 'submission_deadline'  # Added submission_deadline
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def validate(self, data):
        """Check submission deadlines and status transitions"""
        # Get the instance (for update) or create a temporary one (for create)
        instance = self.instance or Course(**data)
        
        # Check submission deadlines for SUBMITTED status
        if data.get('status') == Course.Status.SUBMITTED:
            deadline = data.get('submission_deadline') or instance.submission_deadline
            if deadline and timezone.now() > deadline:
                raise serializers.ValidationError(
                    "Submission deadline has passed"
                )
            
            # Check if all required fields are completed
            if not self._check_required_fields(instance, data):
                raise serializers.ValidationError(
                    "All required fields must be completed before submission"
                )
        
        # Check publishing validation for PUBLISHED status
        if data.get('status') == Course.Status.PUBLISHED:
            # Ensure only approved courses can be published
            if instance.status != Course.Status.APPROVED:
                raise serializers.ValidationError(
                    "Only approved courses can be published"
                )
        
        return data

    def _check_required_fields(self, instance, data):
        """
        Check if all required fields are completed for submission.
        This replaces the missing check_completeness() method.
        """
        required_fields = ['title', 'description', 'objectives', 'contents', 'duration']
        
        for field in required_fields:
            # Use the value from data if provided, otherwise from instance
            value = data.get(field, getattr(instance, field, None))
            
            if not value or (isinstance(value, str) and value.strip() == ''):
                return False
        
        return True
    
    def create(self, validated_data):
        """
        Create a new course instance with associated team members.
        """
        team_members_data = validated_data.pop('team_members', [])
        user = self.context['request'].user
        
        # Authorization check - only specific roles can create courses
        if not (user.is_formateur or user.is_responsable or user.is_admin):
            raise serializers.ValidationError(
                "Only trainers, department heads, or admins can create courses"
            )
        
        # Create course with DRAFT status (not SUBMITTED as commented)
        course = Course.objects.create(
            **validated_data,
            created_by=user,
            status=Course.Status.DRAFT
        )
        
        # Process team members
        self._handle_team_members(course, team_members_data)
        return course
    
    def update(self, instance, validated_data):
        """
        Update an existing course instance and its team members.
        """
        team_members_data = validated_data.pop('team_members', None)
        user = self.context['request'].user
        
        # Authorization check - only creator or admin/responsable can update
        if instance.created_by != user and not (user.is_admin or user.is_responsable):
            raise serializers.ValidationError(
                "You can only update courses you created"
            )
        
        # Update course fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update team members if new data was provided
        if team_members_data is not None:
            self._handle_team_members(instance, team_members_data)
        
        return instance
    
    def _handle_team_members(self, course, members_data):
        """
        Private helper method to manage course-team member relationships.
        """
        # Clear all existing team member associations for this course
        CourseTeam.objects.filter(course=course).delete()
        
        # Create or update team members and associate them with the course
        for member_data in members_data:
            try:
                member, created = TeamMember.objects.get_or_create(
                    email=member_data['email'],  # Use email as unique identifier
                    defaults={
                        'full_name': member_data['full_name'],
                        'qualification': member_data['qualification']
                    }
                )
                
                # If the member already existed, update their information
                if not created:
                    member.full_name = member_data['full_name']
                    member.qualification = member_data['qualification']
                    member.save()
                
                CourseTeam.objects.create(course=course, team_member=member)
                
            except KeyError as e:
                raise serializers.ValidationError(
                    f"Missing required field in team member data: {e}"
                )
            except Exception as e:
                raise serializers.ValidationError(
                    f"Error processing team member: {str(e)}"
                )