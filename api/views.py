from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics,status
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,AllowAny
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
# from django.contrib.auth.models import User
from .models import User
from .serializers import UserRegistrationSerializer
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from datetime import timedelta,datetime
from django.contrib.auth import authenticate


class UserRegistrationView(generics.CreateAPIView):
    queryset =User.objects.all()
    serializer_class=UserRegistrationSerializer
    permission_classes=[AllowAny]

    def create(self,request,*args,**kwargs):

        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.save()
        refresh=RefreshToken.for_user(user)
        refresh['role_model']=user.role_model
        

        response=Response({
            'user':{
                'id':user.id,
                'username':user.username,
                'email':user.email,
                'role_model':user.role_model
            },

        },
        status=status.HTTP_201_CREATED
        )

        cookie_max_age=7*24*60*60 #seconds (7 days)
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False ,
            samesite="Strict",
            max_age=cookie_max_age,
            # expires=datetime.now()+timedelta(seconds=cookie_max_age)

        )

        response.set_cookie(
            'access',
            str(refresh.access_token),
            httponly=False,
            samesite="Strict"

        )
        return response


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

    
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not user.is_active:
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        refresh["role_model"]=user.role_model

        response = Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role_model':user.role_model
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

        # Set cookies
        cookie_max_age = 7 * 24 * 60 * 60  # 7 days in seconds

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,  # true in prod
            samesite='Strict',
            max_age=cookie_max_age
        )

        response.set_cookie(
            key='access',
            value=str(refresh.access_token),
            httponly=False,
            secure=False,  # true in prod https
            samesite='Strict'
        )
        return response
    
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        response = Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)

        # del cookies
        response.delete_cookie('refresh_token')
        response.delete_cookie('access')

        return response
    

class CookieTokenRefreshView(TokenRefreshView):
    serializer_class =TokenRefreshSerializer

    def post(self,request,*args,**kwargs):
        refresh_token=self.request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response ({'error':'Refresh token is missing'},status=400)
        
        serializer=self.get_serializer(data={'refresh':refresh_token})
        serializer.is_valid(raise_exception=True)
        
        response.set_cookie(             
            key='access',
            value=serializer.validated_data['access'],
            httponly=False,
            secure=False,
            samesite='Strict',
        )
        return response



@method_decorator(ensure_csrf_cookie,name='dispatch')
class CSRFTokenView(APIView):
  
  def get(self,request,format=None):
    return Response({'csrfToken':request.META.get('CSRF_COOKIE')})



        

