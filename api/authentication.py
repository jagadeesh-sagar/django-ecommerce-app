from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authenticator that reads the access token from
    the 'access' HttpOnly cookie instead of the Authorization header.

    Order of fallback (set in settings.py DEFAULT_AUTHENTICATION_CLASSES):
      1. CookieJWTAuthentication  — cookie-based JWT  (this class)
      2. JWTAuthentication        — Authorization: Bearer <token>
      3. SessionAuthentication    — Django session / admin
    """

    def authenticate(self, request):
        access_token = request.COOKIES.get('access')

        # No cookie present — let the next authenticator in the list try
        if not access_token:
            return None

        try:
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except (InvalidToken, TokenError) as e:
            # Token is present but invalid/expired
            raise AuthenticationFailed(
                detail={'error': 'Access token is invalid or expired. Please refresh.'},
                code='token_not_valid'
            )