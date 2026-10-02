from django.urls import path
from .views import RegisterView, LoginView, LogoutView, UserMeView, CookieTokenRefreshView, CSRFTokenView

urlpatterns = [
    path('csrf/', CSRFTokenView.as_view(), name='csrf'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', UserMeView.as_view(), name='me'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='refresh'),
]
