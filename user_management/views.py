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
        

class BusinessPreferencesView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating a user's business preferences.

    This view provides authenticated users with the ability to retrieve their
    existing business preferences or update them. If the user's preferences
    do not exist, a 404 response will be returned. The phone number field can 
    also be updated and is validated to ensure uniqueness.

    Permissions:
    - Only authenticated users have access to this endpoint.

    Attributes:
    - permission_classes (list): List of permission classes required for access.
    - serializer_class (BusinessPreferencesSerializer): Serializer class for business preferences.

    Methods:
    - get_object(self): Retrieves the business preferences for the authenticated user, or returns None if not found.
    - get(self, request, *args, **kwargs): Handles GET requests to retrieve business preferences.
    - update(self, request, *args, **kwargs): Handles PUT/PATCH requests to update business preferences, including phone number uniqueness validation.
    - perform_update(self, serializer): Saves the updated preferences to the database.

    Responses:
    - 200 OK: Successfully retrieved or updated business preferences.
    - 404 Not Found: No business preferences found for the user.
    - 400 Bad Request: Validation error if the phone number is already in use.

    Example Request (PUT /api/business-preferences/):
    ```
    {
        "business_field_1": "Updated value",
        "business_field_2": "Another updated value",
        "phone_number": "+1234567890"
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessPreferencesSerializer

    def get_object(self):
        user = self.request.user
        try:
            return BusinessPreferences.objects.get(user=user)
        except BusinessPreferences.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        business_preferences = self.get_object()
        if business_preferences is not None:
            serializer = self.get_serializer(business_preferences)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "No business preferences found for this user."}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        business_preferences = self.get_object()
        if business_preferences is None:
            return Response({"detail": "No business preferences found for this user."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        update_number=request.data.get('phone_number',None)
        # user_data = request.data.get('user', {})
        # phone_number = user_data.get('phone_number')

        if update_number :
            if CustomUser.objects.filter(phone_number=update_number).exclude(id=user.id).exists():
                return Response({"phone_number": "This phone number is already in use."}, status=status.HTTP_400_BAD_REQUEST)
            user.phone_number = update_number
            user.save()

        serializer = self.get_serializer(business_preferences, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
        
        

class VideoPitchUploadView(generics.CreateAPIView):
    """
    View for uploading a video pitch related to business preferences.
    
    This endpoint allows authenticated users to upload a video pitch with a title, 
    description, and a video file. The user ID is automatically associated with the 
    video pitch upon creation.

    Permissions:
    - Only authenticated users can access this endpoint.
    
    Request Body:
    - title (str): The title of the video. Required. Max length 50 characters.
    - description (str): A description of the video. Required. Max length 200 characters.
    - file (file): The video file. Required. Only accepts .mp4, .mov, or .avi files.

    Responses:
    - 201 Created: If the video pitch is successfully uploaded.
    - 400 Bad Request: If validation fails (e.g., missing fields, invalid file type).

    Example:
    ```
    POST /upload-video/
    {
        "title": "My Business Pitch",
        "description": "A brief description of my business idea.",
        "file": "<video_file>"
    }
    ```
    """
    
    queryset = VideoPitch.objects.all()
    serializer_class = VideoPitchSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Associates the current user with the video pitch before saving.

        Parameters:
        - serializer (VideoPitchSerializer): The serializer containing validated data.

        Returns:
        - VideoPitch instance saved with the authenticated user.
        """
        serializer.save(user=self.request.user)


class UploadDocumentView(generics.CreateAPIView):
    """
    API view to upload a document related to business preferences.

    This endpoint allows authenticated users to upload documents with a title, 
    description, and a file. The uploaded document will be associated with the 
    currently logged-in user.

    Permissions:
        - Only authenticated users can upload documents.

    Request Body:
        - document_title: Required. The title of the document.
        - document_description: Required. A description of the document.
        - document_file: Required. The file to be uploaded (must be a PDF, Word document, or Excel file).

    Response:
        - On success, returns the created document details with a 201 status code.
        - On failure, returns validation errors with a 400 status code.
    """

    queryset = DocumentsBusiness.objects.all()
    serializer_class = DocumentsBusinessSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Save the document instance with the associated user.

        This method overrides the default create method to add the currently 
        authenticated user to the document instance being created.

        Args:
            serializer: An instance of the serializer class for the model.
        """
        
        user = self.request.user
        document_title = serializer.validated_data['document_title']
        if DocumentsBusiness.objects.filter(user=user, document_title=document_title).exists():
            raise serializers.ValidationError({'document_title': 'A document with this title already exists for your account.'})
        
        serializer.save(user=self.request.user)
        
        
class CombinedUserDetailView(generics.RetrieveAPIView):
    """
    Retrieve detailed information about the authenticated user.

    This view returns a combined data profile for the authenticated user,
    which includes business-related information. It is accessible only to 
    authenticated users.

    ---
    responses:
      200:
        description: Successfully retrieved user profile data.
        schema:
          $ref: '#/definitions/CombinedDataBusinessProfile'  # Assuming you have this definition in your Swagger schema.
      401:
        description: Unauthorized access, user must be authenticated.
      404:
        description: User not found (this shouldn't happen as it returns the current user).
    """
    serializer_class = CombinedDataBusinessProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class BusinessDocumentDeleteView(generics.DestroyAPIView):
    """
    Delete a business document.

    This view allows authenticated users to delete a specific document 
    related to their business by its ID. The document will be removed from 
    the database.

    ---
    parameters:
      - name: id
        in: path
        required: true
        type: integer
        description: The ID of the business document to be deleted.
    responses:
      204:
        description: Business document successfully deleted.
      401:
        description: Unauthorized access; user must be authenticated.
      404:
        description: Business document not found. The specified document does not exist.
    """
    queryset = DocumentsBusiness.objects.all()
    serializer_class = DocumentsBusinessSerializer
    permission_classes=[IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        document = self.get_object()
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
