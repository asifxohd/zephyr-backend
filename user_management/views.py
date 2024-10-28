# views.py
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from user_authentication.models import Location, Industry
from .serializers import *
from rest_framework.exceptions import NotFound
import json
from rest_framework import status
from rest_framework.views import APIView


class LocationViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing locations.

    Provides operations to list and create locations. 

    Permissions:
        - User must be authenticated.

    Methods:
        GET: List all locations.
        POST: Create a new location.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

class IndustryViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing industries.

    Provides operations to list and create industries.

    Permissions:
        - User must be authenticated.

    Methods:
        GET: List all industries.
        POST: Create a new industry.
    """
    queryset = Industry.objects.all()
    serializer_class = IndustrySerializer
    permission_classes = [IsAuthenticated]
    
class CombinedIndustryLocationView(generics.GenericAPIView):
    """
    API view to retrieve both locations and industries.

    Provides a combined response containing a list of all locations and a list of all industries.

    Methods:
        GET: Retrieve a combined list of locations and industries.
    """
    serializer_class = CombinedIndustryLocationSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve locations and industries.

        Retrieves all locations and industries from the database, serializes them, and returns them
        in a combined response.

        Parameters:
            request (Request): The HTTP request object.

        Returns:
            Response: A response object containing lists of locations and industries.
        """
        locations = Location.objects.all()
        industries = Industry.objects.all()
        
        serializer = CombinedIndustryLocationSerializer({
            'locations': LocationSerializer(locations, many=True).data,
            'industries': IndustrySerializer(industries, many=True).data
        })
        
        return Response(serializer.data)
    
class UserInfoAPIView(generics.GenericAPIView):
    """
    API view to retrieve information about the currently authenticated investor user.

    Returns user information including full name, phone number, email,
    and additional investor preferences (if applicable).

    Permissions:
        - User must be authenticated.
        - User must have the role of 'investor'.

    Methods:
        GET: Retrieve the details of the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserSerializer
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve user information.

        Checks if the current user has the role of 'investor'. If so, returns
        the user data serialized using `CustomUserSerializer`. If not, raises
        a 404 Not Found error.

        Parameters:
            request (Request): The HTTP request object.

        Returns:
            Response: A response object containing user information if successful,
                      or an error message if the user is not an investor.
        """
        user = request.user
        if user.role != 'investor':
            raise NotFound('User is not an investor.')
        
        user_data = CustomUserSerializer(user).data
        return Response(user_data)
    
class InvestorPreferencesUpdateView(generics.RetrieveUpdateAPIView):
    """
        API view to retrieve and update investor preferences for the authenticated user.

        This view allows the authenticated user to retrieve their investor preferences,
        including preferred locations and industries, and to update them. If preferences
        do not exist, they will be created.

        Permissions:
            - User must be authenticated.

        Methods:
            GET: Retrieve the investor preferences of the authenticated user.
            PUT: Update the investor preferences of the authenticated user.

        Request Body for Update:
            - preferred_locations (list): List of preferred location IDs.
            - preferred_industries (list): List of preferred industry IDs.
            - cover_image (file, optional): Image file for the cover.
            - avatar_image (file, optional): Image file for the avatar.
            - description (str, optional): A brief description of the user.

        Responses:
            200 OK: Returns the updated investor preferences.
            400 Bad Request: If the provided IDs are not valid, or if the JSON format is incorrect.
    """
    serializer_class = InvestorPreferencesSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        preferences, created = InvestorPreferences.objects.get_or_create(
            user=self.request.user
        )
        return preferences

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        mutable_data = request.data.copy() if hasattr(request.data, 'copy') else request.data

        try:
            preferred_locations_str = request.data.get('preferred_locations', '[]')
            if preferred_locations_str:
                preferred_locations_ids = json.loads(preferred_locations_str)
                preferred_locations_ids = [int(pk) for pk in preferred_locations_ids]
                locations = Location.objects.filter(id__in=preferred_locations_ids)
                instance.preferred_locations.set(locations)

            preferred_industries_str = request.data.get('preferred_industries', '[]')
            if preferred_industries_str:
                preferred_industries_ids = json.loads(preferred_industries_str)
                preferred_industries_ids = [int(pk) for pk in preferred_industries_ids]
                industries = Industry.objects.filter(id__in=preferred_industries_ids)
                instance.preferred_industries.set(industries)

            serializer = self.get_serializer(
                instance, 
                data=mutable_data, 
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            instance.refresh_from_db()
            return Response(self.get_serializer(instance).data)

        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON format for locations or industries'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError:
            return Response(
                {'error': 'Invalid ID format in locations or industries'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_update(self, serializer):
        serializer.save()
        
class BusinessPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            business_preferences = BusinessPreferences.objects.get(user=user)
            serializer = BusinessPreferencesSerializer(business_preferences)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BusinessPreferences.DoesNotExist:
            return Response({"detail": "No business preferences found for this user."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        try:
            business_preferences = BusinessPreferences.objects.get(user=user)
            serializer = BusinessPreferencesSerializer(business_preferences, data=data, partial=True)
        except BusinessPreferences.DoesNotExist:
            serializer = BusinessPreferencesSerializer(data=data)

        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
