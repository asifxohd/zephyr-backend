# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CommentViewSet, LikeViewSet, ShareViewSet, CommentListView, ToggleLikePostView,PostViewForRequestUser
router = DefaultRouter()
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'likes', LikeViewSet)
router.register(r'shares', ShareViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('posts/<int:post_id>/comments/', CommentListView.as_view(), name='post-comments'),
    path('toggle-like/', ToggleLikePostView.as_view(), name='toggle_like_post'),
    path('user/posts/', PostViewForRequestUser.as_view(), name='user-posts'),

]
