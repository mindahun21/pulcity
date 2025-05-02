from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from ..models import CustomUser, OTP
from .serializers import (
    RegisterSerializer,
    OrganizationRegisterSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    ResendOtpSerializer,
)
from ..serializers import(
  UserSerializer,
  UserWithAnyProfileDocSerializer,
  UserWithOrganizationProfileDocSerializer
)
from ..utils import send_verification_email, get_tokens_for_user
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

@extend_schema(tags=["Auth"],responses={
  200:OpenApiResponse(
    inline_serializer(
      name="UserRegisterResponse",
      fields={
        "message":serializers.CharField(),
        "user":UserWithAnyProfileDocSerializer()
      }
    )
  ),
  400:OpenApiResponse(
    inline_serializer(
        name="UserRegisterErrorResponse",
        fields={
            "field_name": serializers.ListField(
                child=serializers.CharField(),
                help_text="A list of error messages for the field.",
            ),
        },
    ),
    description="Validation errors from from register.",
  )
})
class RegisterView(APIView):
  permission_classes = [AllowAny]
  serializer_class = RegisterSerializer
  
  
  def post(self, request):
      serializer = self.serializer_class(data=request.data)
      if serializer.is_valid():
          user = serializer.save()
          user.is_active = False
          user.save()
          serialized_user = UserSerializer(user).data
          send_verification_email.delay(user_id=user.id, purpose="Email Verification OTP")

          return Response({"message": "User registered. Please verify your email.","user":serialized_user}, status=status.HTTP_201_CREATED)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Auth"],responses={
  200:OpenApiResponse(
    inline_serializer(
      name="UserRegisterResponse",
      fields={
        "message":serializers.CharField(),
        "user":UserWithOrganizationProfileDocSerializer()
      }
    )
  ),
  400:OpenApiResponse(
    inline_serializer(
        name="UserRegisterErrorResponse",
        fields={
            "field_name": serializers.ListField(
                child=serializers.CharField(),
                help_text="A list of error messages for the field.",
            ),
        },
    ),
    description="Validation errors from from register.",
  )
})
class OrganizationRegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = OrganizationRegisterSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.save()
            serialized_user = UserSerializer(user).data

            send_verification_email.delay(user_id=user.id, purpose="Email Verification OTP")

            return Response({"message": "Organization registered. Please verify your email.","user":serialized_user}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Auth"],
    responses={
        200: OpenApiResponse(
            inline_serializer(
                name="VerifyEmailSuccessResponse",
                fields={
                    "message": serializers.CharField(),
                    "tokens": serializers.DictField(),
                    "user": UserSerializer(),
                },
            ),
            description="Email successfully verified.",
        ),
        400: OpenApiResponse(
            inline_serializer(
                name="VerifyEmailErrorResponse",
                fields={
                    "error": serializers.DictField(
                        child=serializers.CharField(),
                        help_text="Error details for invalid OTP or expired OTP.",
                    ),
                },
            ),
            description="Invalid OTP or OTP expired.",
        ),
        404: OpenApiResponse(
            inline_serializer(
                name="VerifyEmailNotFoundResponse",
                fields={
                    "error": serializers.DictField(
                        child=serializers.CharField(),
                        help_text="Error details for user not found.",
                    ),
                },
            ),
            description="User not found.",
        ),
    },
)
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = request.data.get('email')
            otp = request.data.get('otp')

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'error': {'message': 'User not found'}}, status=status.HTTP_404_NOT_FOUND)

            try:
                otp_instance = OTP.objects.get(user=user, otp=otp)
            except OTP.DoesNotExist:
                return Response({'error': {'otp': 'Invalid OTP Please enter the correct one'}}, status=status.HTTP_400_BAD_REQUEST)

            if otp_instance.is_expired:
                send_verification_email.delay(user_id=user.id, purpose="Email Verification OTP")
                return Response({'error': {'otp': f'Otp is expired! we have sent New otp to {user.email} '}}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.last_login = timezone.now()
            user.save()
            otp_instance.delete()
            tokens = get_tokens_for_user(user)

            serialized_user = UserSerializer(user).data
            return Response({
                'message': 'Email successfully verified.',
                'tokens': tokens,
                'user': serialized_user,
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  
@extend_schema(
    tags=["Auth"],
    request=ResendOtpSerializer,  # Input serializer
    responses={
        200: OpenApiResponse(
            inline_serializer(
                name="ResendOtpSuccessResponse",
                fields={
                    "message": serializers.CharField(),
                },
            ),
            description="OTP code has been resent successfully.",
        ),
        400: OpenApiResponse(
            inline_serializer(
                name="ResendOtpErrorResponse",
                fields={
                    "field_name": serializers.ListField(
                        child=serializers.CharField(),
                        help_text="A list of error messages for the field.",
                    ),
                },
            ),
            description="Validation errors from ResendOtpSerializer.",
        ),
        404: OpenApiResponse(
            inline_serializer(
                name="ResendOtpNotFoundResponse",
                fields={
                    "error": serializers.DictField(
                        child=serializers.CharField(),
                        help_text="Error details for user not found.",
                    ),
                },
            ),
            description="User not found.",
        ),
    },
)
class ResendOtpView(APIView):
  permission_classes = [AllowAny]
  serializer_class = ResendOtpSerializer

  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      email = request.data.get('email')
      
      try:
        user = CustomUser.objects.get(email=email)
      except CustomUser.DoesNotExist:
        return Response({'error':{'message': 'User not found'}}, status=status.HTTP_404_NOT_FOUND)

      otps = OTP.objects.filter(user=user)
      otps.delete()
      send_verification_email.delay(user_id=user.id, purpose="Email Verification OTP")


      return Response({'message': 'OTP code has been resent'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Auth"],
    request=LoginSerializer,  # Input serializer
    responses={
        200: OpenApiResponse(
            inline_serializer(
                name="LoginSuccessResponse",
                fields={
                    "tokens": serializers.DictField(),
                    "user": UserSerializer(),
                },
            ),
            description="Login successful.",
        ),
        400: OpenApiResponse(
            inline_serializer(
                name="LoginValidationErrorResponse",
                fields={
                    "field_name": serializers.ListField(
                        child=serializers.CharField(),
                        help_text="A list of error messages for the field.",
                    ),
                },
            ),
            description="Validation errors from LoginSerializer.",
        ),
        401: OpenApiResponse(
            inline_serializer(
                name="LoginUnauthorizedResponse",
                fields={
                    "error": serializers.CharField(),
                },
            ),
            description="Invalid credentials.",
        ),
        403: OpenApiResponse(
            inline_serializer(
                name="LoginForbiddenResponse",
                fields={
                    "error": serializers.CharField(),
                },
            ),
            description="User email is not verified.",
        ),
    },
)
class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                if not user.is_active:
                    return Response({"error": "Please verify your email."}, status=status.HTTP_403_FORBIDDEN)
                tokens = get_tokens_for_user(user)
                serialized_user = UserSerializer(user).data
                return Response({"tokens": tokens, 'user':serialized_user}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Auth"],
    request=ResetPasswordSerializer,  # Input serializer
    responses={
        200: OpenApiResponse(
            inline_serializer(
                name="ResetPasswordSuccessResponse",
                fields={
                    "message": serializers.CharField(),
                },
            ),
            description="Password has been reset successfully.",
        ),
        400: OpenApiResponse(
            inline_serializer(
                name="ResetPasswordValidationErrorResponse",
                fields={
                    "field_name": serializers.ListField(
                        child=serializers.CharField(),
                        help_text="A list of error messages for the field.",
                    ),
                },
            ),
            description="Validation errors from ResetPasswordSerializer.",
        ),
    },
)
class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
