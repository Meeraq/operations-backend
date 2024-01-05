from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Affiliate, Lead
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from api.models import (
    Role,
    Profile,
    SentEmailActivity,
    OTP,
    UserToken,
    UserLoginActivity,
)
from api.serializers import PmoDepthOneSerializer
import json
import string
import random
from .serializer import AffiliateSerializer, AffiliateDepthOneSerializer, LeadSerializer
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.shortcuts import render, get_object_or_404
import environ
from operationsBackend import settings
from django.contrib.auth import authenticate, login, logout
from rest_framework.exceptions import AuthenticationFailed

env = environ.Env()
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.crypto import get_random_string


def create_send_email(user_email, file_name):
    try:
        user = User.objects.get(username=user_email)
        sent_email = SentEmailActivity.objects.create(
            user=user,
            email_subject=file_name,
            timestamp=timezone.now(),
        )
        sent_email.save()
    except Exception as e:
        pass


def send_mail_templates(file_name, user_email, email_subject, content, bcc_emails):
    try:
        email_message = render_to_string(file_name, content)

        email = EmailMessage(
            f"{env('EMAIL_SUBJECT_INITIAL',default='')} {email_subject}",
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            user_email,
            bcc_emails,
        )
        email.content_subtype = "html"

        email.send(fail_silently=False)
        for email in user_email:
            create_send_email(email, file_name)
    except Exception as e:
        print(f"Error occurred while sending emails: {str(e)}")


def get_user_data(user):
    if not user.profile:
        return None
    elif user.profile.roles.count() == 0:
        return None
    user_profile_role = user.profile.roles.all().first().name
    roles = []
    for role in user.profile.roles.all():
        roles.append(role.name)
    if user_profile_role == "pmo":
        serializer = PmoDepthOneSerializer(user.profile.pmo)
    elif user_profile_role == "affiliate":
        serializer = AffiliateDepthOneSerializer(user.profile.affiliate)
    else:
        return None

    
    return {
        **serializer.data,
        "roles": roles,
        "user": {**serializer.data["user"], "type": user_profile_role},
    }


# Create your views here.
class AddAffiliate(APIView):
    def post(self, request, *args, **kwargs):
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        email = request.data.get("email")
        phone = request.data.get("phone")

        if not all([first_name, last_name, email, phone]):
            return Response(
                {"error": "All required fields must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create the Django User
            if Affiliate.objects.filter(email=email).exists():
                return Response(
                    {"error": "Affiliate with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                # Check if the user already exists
                user = User.objects.filter(email=email).first()
                if not user:
                    temp_password = "".join(
                        random.choices(
                            string.ascii_uppercase
                            + string.ascii_lowercase
                            + string.digits,
                            k=8,
                        )
                    )
                    user = User.objects.create_user(
                        username=email, password=temp_password, email=email
                    )
                    profile = Profile.objects.create(user=user)

                else:
                    profile = Profile.objects.get(user=user)

                affiliate_role, created = Role.objects.get_or_create(name="affiliate")
                profile.roles.add(affiliate_role)
                profile.save()

                # Create the Coach User using the Profile
                affiliate_user = Affiliate.objects.create(
                    user=profile,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    is_approved=False,
                )

                affiliate_serializer = AffiliateSerializer(affiliate_user)

            return Response({"affiliate": affiliate_serializer.data})

        except Exception as e:
            # Return error response if any other exception occurs
            print(e)
            return Response(
                {"error": "An error occurred while registering."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_otp(request):
    try:
        user = User.objects.get(username=request.data["email"])

        try:
            # Check if OTP already exists for the user
            otp_obj = OTP.objects.get(user=user)
            otp_obj.delete()
        except OTP.DoesNotExist:
            pass

        # Generate OTP and save it to the database
        otp = get_random_string(length=6, allowed_chars="0123456789")
        created_otp = OTP.objects.create(user=user, otp=otp)

        user_data = get_user_data(user)

        name = user_data.get("name") or user_data.get("first_name") or "User"
        # Send OTP on email to learner
        subject = f"Meeraq Login OTP"
        message = (
            f"Dear {name} \n\n Your OTP for login on meeraq portal is {created_otp.otp}"
        )
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.username])
        microsoft_auth_url = (
            f'{env("BACKEND_URL")}/api/microsoft/oauth/{request.data["email"]}/'
        )
        user_token_present = False
        try:
            user_token = UserToken.objects.get(
                user_profile__user__username=request.data["email"]
            )
            if user_token:
                user_token_present = True
        except Exception as e:
            pass
        send_mail_templates(
            "hr_emails/login_with_otp.html",
            [user],
            subject,
            {
                "name": name,
                "otp": created_otp.otp,
                "email": request.data["email"],
                "microsoft_auth_url": microsoft_auth_url,
                "user_token_present": user_token_present,
            },
            [],  # no bcc
        )
        return Response({"message": f"OTP has been sent to {user.username}!"})

    except User.DoesNotExist:
        # Handle the case where the user with the given email does not exist
        return Response(
            {"error": "User with the given email does not exist."}, status=400
        )

    except Exception as e:
        # Handle any other exceptions
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_otp(request):
    otp_obj = (
        OTP.objects.filter(
            user__username=request.data["email"], otp=request.data["otp"]
        )
        .order_by("-created_at")
        .first()
    )
    data = request.data
    platform = data.get("platform", "unknown")

    if otp_obj is None:
        raise AuthenticationFailed("Invalid OTP")

    user = otp_obj.user
    # token, created = Token.objects.get_or_create(user=learner.user.user)
    # Delete the OTP object after it has been validated
    user_email = request.data["email"]
    otp_obj.delete()
    last_login = user.last_login
    login(request, user)

    user_data = get_user_data(user)

    if user_data:
        login_timestamp = timezone.now()
        UserLoginActivity.objects.create(
            user=user, timestamp=login_timestamp, platform=platform
        )

        return Response(
            {
                "detail": "Successfully logged in.",
                "user": {**user_data, "last_login": last_login},
            }
        )
    else:
        logout(request)
        return Response({"error": "Invalid user type"}, status=400)



@api_view(['POST'])
def lead_create_view(request):
    if request.method == 'POST':
        serializer = LeadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['GET'])
def leads_by_affiliate(request, affiliate_id):
    try:
        affiliate = Affiliate.objects.get(pk=affiliate_id)
    except Affiliate.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    print("affiliate_id", affiliate_id)
    leads = Lead.objects.filter(affiliate=affiliate)
    print("leads", leads)
    serializer = LeadSerializer(leads, many=True)
    return Response(serializer.data)



@api_view(['PUT'])
def lead_update(request, pk):
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = LeadSerializer(lead, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def all_leads(request):
    
    leads = Lead.objects.all()
    serializer = LeadSerializer(leads, many=True)
    return Response(serializer.data)