import random
from django.core.mail import send_mail
from .models import OTP
from django.conf import settings
from celery import shared_task
from rest_framework_simplejwt.tokens import RefreshToken
  
def generate_otp():
    """Generate a 6-digit random OTP."""
    return random.randint(100000, 999999)

@shared_task
def send_verification_email(user_id, purpose="2FA", method="email"):
    from user.models import CustomUser 
    user = CustomUser.objects.get(id=user_id)

    otp = generate_otp()
    OTP.objects.filter(user=user).delete()

    OTP.objects.create(user=user, otp=otp)

    subject = f"Your {purpose} OTP Code"
    message = f"Your OTP for {purpose} is: {otp}. It will expire in 5 minutes."

    if method == "email":
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        return True
    elif method == "sms":
        print(f"Sending SMS to {user.phone_number}: {message}")
        return True

    return False



def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }