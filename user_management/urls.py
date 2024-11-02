from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'industries', IndustryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('combined-location-industry/', CombinedIndustryLocationView.as_view(), name='combined-data'),
    path('investor-user-info/', UserInfoAPIView.as_view(), name='user-info'),
    path('user/update/', InvestorPreferencesUpdateView.as_view(), name='user-update'),
    path('business-preferences/', BusinessPreferencesView.as_view(), name='business-preferences-detail'),
    path('business-upload-video/', VideoPitchUploadView.as_view(), name='VideoPitchUploadView'),
    path('upload-document/', UploadDocumentView.as_view(), name='upload-document'),
    path('business-profile-info/', CombinedUserDetailView.as_view(), name='combined_user_detail'),
    path('delete-document/<int:pk>/', BusinessDocumentDeleteView.as_view(), name='document-delete'),
    path('fetch-investor-users-info/', InvestorPreferencesListView.as_view(), name='investor-users-info'),
    path('investors/search/', InvestorSearchView.as_view(), name='investor-serach-users-info'),
    path('update-user-status/<int:id>/', ToggleUserStatus.as_view(), name='update-user-status'),
    path('admin-investor-user-info/<int:pk>/', AdminInvestorUserDetailAPIView.as_view(), name='user-detail'),
    path('admin/business-users/', ListBusinessUsersInAdminView.as_view(), name='list_business_users_admin'),
    path('admin/business/search/', AdminBusinessSearchView.as_view(), name='business-serach-admin-side-info'),
    path('admin/business/individual-business-info/<int:pk>/', RetrieveSpecificUserDetailedBusinessProfileView.as_view(), name='retrieve_specific_user_detailed_business_profile'),

]
