from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class CSRFTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'success': 'CSRF cookie set'})

from rest_framework.throttling import ScopedRateThrottle

class RegisterView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'anon'
    serializer_class = RegisterSerializer

class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(email=email, password=password)
        if user is not None:
            tokens = get_tokens_for_user(user)
            res = Response({'success': 'Logged in successfully'})
            
            res.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'], 
                value=tokens['access'],
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            res.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], 
                value=tokens['refresh'],
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            return res
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

from .authentication import JWTCookieAuthentication

class LogoutAuth(JWTCookieAuthentication):
    def authenticate(self, request):
        self.enforce_csrf(request)
        return None

class LogoutView(APIView):
    authentication_classes = [LogoutAuth]
    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        res = Response({'success': 'Logged out successfully'})
        
        cookie_attrs = {
            'max_age': 0,
            'expires': 'Thu, 01 Jan 1970 00:00:00 GMT',
            'secure': settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            'httponly': settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            'samesite': settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        }
        
        res.set_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'], '', **cookie_attrs)
        res.set_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], '', **cookie_attrs)
        return res

from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

@method_decorator(never_cache, name='dispatch')
class UserMeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class CookieTokenRefreshView(APIView):
    authentication_classes = [LogoutAuth]
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'anon'

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token is None:
            return Response({'error': 'Refresh token missing'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access = str(refresh.access_token)
            
            res = Response({'success': 'Token refreshed'})
            res.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'], 
                value=access,
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            return res
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
