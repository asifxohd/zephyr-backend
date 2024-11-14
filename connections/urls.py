from django.urls import path
from .views import (
    FollowUserView,
    FollowersListView,
    FollowingListView,
    CheckFollowStatusView,
    UserConnectionsView,
    UserFollowersFollowingView,
    SuggestedUsersView,
)

urlpatterns = [
    path("users/<int:user_id>/follow/", FollowUserView.as_view(), name="follow-user"),
    path(
        "users/<int:user_id>/followers/",
        FollowersListView.as_view(),
        name="followers-list",
    ),
    path(
        "users/<int:user_id>/following/",
        FollowingListView.as_view(),
        name="following-list",
    ),
    path(
        "check-follow-status/<int:business_id>/",
        CheckFollowStatusView.as_view(),
        name="check-follow-status",
    ),
    path("user-connections/", UserConnectionsView.as_view(), name="user-connections"),
    path(
        "user-social-network/<int:user_id>/",
        UserFollowersFollowingView.as_view(),
        name="user-followers-following",
    ),
    path('suggested-users/', SuggestedUsersView.as_view(), name='suggested-users'),

]
