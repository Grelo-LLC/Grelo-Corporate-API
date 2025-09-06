import logging
import jwt
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.mail import send_mail
from datetime import timedelta
from oauth2_provider.models import get_access_token_model
from .models import BusinessUser, BusinessUserProfile, OTPToken
from api.utils import (
    is_email_valid, is_password_valid,
    generate_user_otp_token, BaseAPIException, 
    upload_profile_image_as_base64, check_tax_id
)

logger = logging.getLogger(__name__)


def expire_existing_otp_token(user):
    return OTPToken.objects.filter(user=user, is_expired=False).update(is_expired=True)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data

        business_email = data.get('business_email')
        business_name = data.get('business_name')
        tax_id = data.get('tax_id')
        country = data.get('country')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not all([business_email, password, tax_id, country, confirm_password, business_name]):
            return Response({"alert": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if BusinessUser.objects.filter(business_email=business_email).exists():
            return Response({"alert": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if BusinessUser.objects.filter(tax_id=tax_id).exists():
            return Response({"alert": "TAX ID already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if not is_email_valid(business_email):
            return Response({"alert": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)
        
        is_valid, message = check_tax_id(tax_id)
        if not is_valid:
            return Response({"alert": message}, status=status.HTTP_400_BAD_REQUEST)
        
        if not is_password_valid(password):
            return Response({"alert": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
        
        if password != confirm_password:
            return Response({"alert": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = BusinessUser.objects.create_user(
                business_email=business_email,
                business_name=business_name,
                tax_id=tax_id,
                country=country,
                password=password,
                is_active=True
            )
            
            BusinessUserProfile.objects.create(user=user)

            return Response({"success": True, "message": "Business user registered successfully"}, status=status.HTTP_201_CREATED)

        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class GetTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        tax_id = request.data.get('tax_id')
        password = request.data.get('password')
        
        is_valid, message = check_tax_id(tax_id)
        if not is_valid:
            return Response({"alert": message}, status=status.HTTP_400_BAD_REQUEST)
        
        if not password:
            return JsonResponse({"error": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not is_password_valid(password):
            return JsonResponse({"error": "Invalid password format."}, status=status.HTTP_400_BAD_REQUEST)

        user = BusinessUser.objects.filter(tax_id=tax_id).first()
        if not user:
            return JsonResponse({"error": "TAX ID not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return JsonResponse({"error": "Incorrect password."}, status=status.HTTP_401_UNAUTHORIZED)


        req = requests.post(
            settings.ROOT_URL + "/o/token/", 
            data={ 
                'grant_type': 'password', 
                'username': tax_id,
                'password': password, 
                'client_id': settings.CLIENT_ID, 
                'client_secret': settings.CLIENT_SECRET
            }
        )

        return JsonResponse(req.json(), status=req.status_code)
    
    
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        req = requests.post(
            settings.ROOT_URL + "/o", 
            data={ 
                'grant_type': 'refresh_token', 
                'refresh_token': request.data.get('refresh_token'), 
                'client_id': settings.CLIENT_ID, 
                'client_secret': settings.CLIENT_SECRET
            }
        )
        
        return JsonResponse(req.json(), status=req.status_code)
    

class RevokeTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        req = requests.post(
            settings.ROOT_URL + "/o/revoke_token", 
            data={ 
                'token': request.data.get('token'), 
                'client_id': settings.CLIENT_ID, 
                'client_secret': settings.CLIENT_SECRET
            }
        )
        
        if req.status_code == 200:
            return JsonResponse({"success": True}, status=req.status_code)
        elif req.status_code == 400:
            return JsonResponse({"error": "Invalid token"}, status=req.status_code)
        return JsonResponse(req.json(), status=req.status_code)
    
    
class CheckTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        tax_id = request.data.get('tax_id')
        password = request.data.get('password')
        
        if not tax_id or not password:
            return Response({'error': 'TAX ID and password are required'}, status=400)
        
        user = BusinessUser.objects.filter(tax_id=tax_id).first()
        if not user:
            return Response({'error': 'User not found'}, status=404)
        
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=401)
        
        AccessToken = get_access_token_model()
        token = AccessToken.objects.filter(user=user, expires__gt=timezone.now()).first()
        
        if token:
            return Response({
                'active': True,
                'access_token': token.token,
                'expires': token.expires
            })
        else:
            return Response({'active': False, 'error': 'No valid token found'}, status=401)
        
        
class OTPCreateView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            business_email = request.data.get('email')
            if not business_email:
                return JsonResponse({"error": "Email is required"}, status=400)

            user = BusinessUser.objects.filter(business_email=business_email).first()
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)

            expire_existing_otp_token(user)

            generated_otp = generate_user_otp_token(business_email)
            OTPToken.objects.create(user=user, otp=generated_otp)

            send_mail(
                subject="OTP for Password Reset",
                message=f"Your OTP code is: {generated_otp}. It is valid for 5 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[business_email],
                fail_silently=False,
            )

            return JsonResponse({"success": True, "message": "An OTP code has been successfully sent to your email address"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
        
class OTPValidateView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            business_email = request.data.get('business_email')
            otp = request.data.get('otp')

            user = BusinessUser.objects.filter(business_email=business_email).first()
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)

            expiration_limit = timezone.now() - timedelta(minutes=5)

            otp_obj = OTPToken.objects.filter(
                user=user,
                otp=otp,
                is_expired=False,
                is_approved=False,
                created_time__gt=expiration_limit
            ).first()

            if not otp_obj:
                return JsonResponse({"error": "OTP is invalid or expired"}, status=400)

            otp_obj.is_approved = True
            otp_obj.save()

            return JsonResponse({"success": True, "message": "OTP verification successful"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
        
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            business_email = request.data.get('business_email')
            password = request.data.get('password')
            confirm_password = request.data.get('confirm_password')
            otp = request.data.get('otp')

            if not all([business_email, password, confirm_password, otp]):
                return JsonResponse({"error": "All fields are required"}, status=400)

            if not is_email_valid(business_email):
                return JsonResponse({"error": "Invalid email format"}, status=400)
            
            if not is_password_valid(password) or not is_password_valid(confirm_password):
                return JsonResponse({"error": "Invalid password format"}, status=400)
            
            if password != confirm_password:
                return JsonResponse({"error": "Passwords do not match"}, status=400)

            user = BusinessUser.objects.filter(business_email=business_email).first()
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)

            expiration_limit = timezone.now() - timedelta(minutes=5)
            otp_obj = OTPToken.objects.filter(
                user=user,
                otp=otp,
                is_approved=True,
                is_expired=False,
                created_time__gt=expiration_limit
            ).first()

            if not otp_obj:
                return JsonResponse({"error": "OTP is invalid or has expired"}, status=400)

            user.set_password(password)
            user.save()

            otp_obj.is_expired = True
            otp_obj.save()

            return JsonResponse({"success": True, "message": "Password has been successfully updated"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)