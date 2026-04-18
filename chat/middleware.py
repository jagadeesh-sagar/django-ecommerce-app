from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken,TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from http.cookies import SimpleCookie
from asgiref.sync import sync_to_async


User=get_user_model()

def get_token_from_scope(scope):

    '''
    Try 3 sources in order:
    1. Cookie (access_token) — matches your DRF CookieJWTAuthentication
    2. Query param (?token=)  — for clients that can't set cookies
    3. None
    '''

    # 1.try cookie

    headers = dict(scope.get("headers", []))
    raw_cookie = headers.get(b"cookie", b"")
    raw_cookie = raw_cookie.decode() if raw_cookie else ""

    if raw_cookie:
        cookie=SimpleCookie()
        cookie.load(raw_cookie)
        if "access_token" in cookie:
            return cookie['access_token'].value
        
    
    # 2 . Try query param
    query_string = parse_qs(scope.get("query_string", b"").decode())
    token = query_string.get("token", [None])[0]
    if token:
        return token
    
    return None


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        close_old_connections()

        scope['user']=AnonymousUser()
        token=get_token_from_scope(scope)

        if token:
            try:
                UntypedToken(token)
                jwt_auth=JWTAuthentication()

                class FakeRequest:
                    META={"HTTP_AUTHORIZATION":f"Bearer {token}"}

                raw_token = jwt_auth.get_raw_token(jwt_auth.get_header(FakeRequest()))
                validated_token = jwt_auth.get_validated_token(raw_token)
                user = await sync_to_async(jwt_auth.get_user)(validated_token) 
                scope["user"] = user
                
            except (InvalidToken,TokenError):
                scope["user"]=AnonymousUser()


        return await super().__call__(scope, receive, send)