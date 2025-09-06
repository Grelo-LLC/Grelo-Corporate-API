from django.urls import path, include
from .views import (
    RegisterView, GetTokenView, RefreshTokenView, RevokeTokenView, CheckTokenView,
    OTPCreateView, OTPValidateView, PasswordResetView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', GetTokenView.as_view(), name='login'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('token/revoke/', RevokeTokenView.as_view(), name='token-revoke'),
    path("token/check/",CheckTokenView.as_view(),name='auth_check'),
    path('otp/create/', OTPCreateView.as_view(), name='otp'),
    path('otp/validate/', OTPValidateView.as_view(), name='otp-validate'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
]