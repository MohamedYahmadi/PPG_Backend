from django.urls import path
from .views import IssueFineAPIView, CreateDisputeAPIView, FineViewSet

urlpatterns = [
    path('issue/', IssueFineAPIView.as_view(), name='api_fine_issue'),
    path('dispute/', CreateDisputeAPIView.as_view(), name='api_dispute_create'),
    path('all/', FineViewSet.as_view({'get': 'list'}), name='api_fines_list'),
]
