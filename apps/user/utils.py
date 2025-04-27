import random
from django.core.mail import send_mail
from .models import OTP
from django.conf import settings
from celery import shared_task
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)
  
def generate_otp():
    """Generate a 6-digit random OTP."""
    return random.randint(100000, 999999)


@shared_task
def send_verification_email(user_id, purpose="2FA", method="email"):
    logger.info(f"Running email task for user {user_id} with purpose {purpose}")

    from apps.user.models import CustomUser 
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist.")
        return False

    otp = generate_otp()
    OTP.objects.filter(user=user).delete()

    OTP.objects.create(user=user, otp=otp)

    subject = f"Your {purpose} OTP Code"
    message = f"Your OTP for {purpose} is: {otp}. It will expire in 5 minutes."

    if method == "email":
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,  
            )
            logger.info(f"Verification email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            user.delete()
            return False
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
    

class ResponsePagination(PageNumberPagination):
  page_size = 10
