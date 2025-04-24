from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('register/',views.RegisterView.as_view(), name="user_register"),
    path('organization/register/', views.OrganizationRegisterView.as_view(),name="organization-register"),
    path('otp/resend/', views.ResendOtpView.as_view(), name="resend-otp"),
    path('email/verify/',views.VerifyEmailView.as_view(), name="verify-email" ),
    path('login/',views.LoginView.as_view(),name="login"),
    path('password/reset/',views.ResetPasswordView.as_view(), name="reset-password"),
]
