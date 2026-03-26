from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, VisitCounterView

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')

urlpatterns = [
    path('', include(router.urls)),
    path('visits/', VisitCounterView.as_view(), name='visit-counter'), 
]