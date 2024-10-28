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

]
