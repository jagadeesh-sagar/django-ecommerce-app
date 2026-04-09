from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from .models import User
from .serializers import UserRegistrationSerializer


REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds

COOKIE_DEFAULTS = dict(
    httponly=True,
    secure=False,       # True in production (HTTPS)
    samesite='Strict',
)


def _set_auth_cookies(response, access_token: str, refresh_token: str = None):
    """Attach JWT cookies to a response object."""
    response.set_cookie(
        key='access',
        value=access_token,
        httponly=False,     # intentionally readable by JS so the frontend
                            # can decode the payload (role, exp, etc.)
        secure=False,       # True in prod
        samesite='Strict',
    )
    if refresh_token:
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=REFRESH_COOKIE_MAX_AGE,
            **COOKIE_DEFAULTS,
        )


def _delete_auth_cookies(response):
    """Remove JWT cookies.  Attributes must mirror set_cookie or some
    browsers silently ignore the delete."""
    response.delete_cookie('access',         samesite='Strict')
    response.delete_cookie('refresh_token',  samesite='Strict')

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        refresh['role_model'] = user.role_model   # embed role in token payload

        response = Response(
            {
                'user': {
                    'id':         user.id,
                    'username':   user.username,
                    'email':      user.email,
                    'role_model': user.role_model,
                },
                # access token also in body so API clients (Postman, MCP) can
                # use Authorization: Bearer
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Registration successful',
            },
            status=status.HTTP_201_CREATED,
        )

        _set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # login() creates a Django session — required for SessionAuthentication
        # and Django admin to work.  Safe to keep alongside JWT.
        login(request, user)

        refresh = RefreshToken.for_user(user)
        refresh['role_model'] = user.role_model

        response = Response(
            {
                'user': {
                    'id':         user.id,
                    'username':   user.username,
                    'email':      user.email,
                    'role_model': user.role_model,
                },
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Login successful',
            },
            status=status.HTTP_200_OK,
        )

        _set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Attempt to blacklist the refresh token if BLACKLIST app is installed.
        # Silently skipped if the token is missing or already blacklisted.
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass  # already expired / invalid 

     
        logout(request)

        response = Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        _delete_auth_cookies(response)
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Reads the refresh token from the HttpOnly 'refresh_token' cookie
    instead of the request body, then writes the new access (and optionally
    rotated refresh) token back into cookies.
    """
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token cookie is missing'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data={'refresh': refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken) as e:
            return Response(
                {'error': 'Refresh token is invalid or expired. Please log in again.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        new_access = serializer.validated_data['access']
        # ROTATE_REFRESH_TOKENS=True in SIMPLE_JWT produces a new refresh token
        new_refresh = serializer.validated_data.get('refresh')

        response = Response(
            {'access': new_access, 'message': 'Token refreshed'},
            status=status.HTTP_200_OK,
        )

        _set_auth_cookies(
            response,
            access_token=new_access,
            refresh_token=new_refresh,   # None -> _set_auth_cookies skips it
        )
        return response


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    """
    GET /api/csrf/
    Returns the CSRF token in JSON and also sets it as a cookie via the
    ensure_csrf_cookie decorator.  Call this once on app load from the
    frontend before any mutating request.
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        # get_token() guarantees the token is generated and stored in the
        # session/cookie — request.META.get('CSRF_COOKIE') can be None
        # if the middleware hasn't run the response phase yet.
        return Response({'csrfToken': get_token(request)})