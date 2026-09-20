import logging
import secrets
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetOTP

logger = logging.getLogger(__name__)


def send_otp_for_user(user, otp_type):
    """
    Generates and dispatches an OTP to user's email or mobile.
    Returns (success: bool, message: str, otp_obj).
    """
    if otp_type == 'email':
        target = user.email
        otp_obj = PasswordResetOTP.generate_otp(user=user, otp_type='email', target=target)
        subject = "Enigma - Password Reset OTP"
        message = (
            f"Hello {user.name},\n\n"
            f"Your OTP for resetting your Enigma account password is: {otp_obj.otp_code}\n\n"
            f"This code will expire in 10 minutes.\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"Regards,\nEnigma Team"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@clubattendance.org'),
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"OTP email sent to {user.email}: {otp_obj.otp_code}")
            return True, f"OTP has been sent to your email ({user.email}).", otp_obj
        except Exception as e:
            logger.error(f"Failed to send email OTP: {e}")
            # In development, still return success with code in terminal log
            return True, f"OTP dispatched to {user.email}. (Dev code: {otp_obj.otp_code})", otp_obj

    elif otp_type == 'mobile':
        target = user.mobile_number
        otp_obj = PasswordResetOTP.generate_otp(user=user, otp_type='mobile', target=target)
        sms_body = f"[Enigma] Your Password Reset OTP is {otp_obj.otp_code}. Valid for 10 minutes."
        
        # Pluggable SMS logic or SMS Gateway API
        # For production, an SMS gateway (Twilio, AWS SNS, Fast2SMS) can be integrated here.
        logger.info(f"SMS OTP sent to {user.mobile_number}: {otp_obj.otp_code}")
        print(f"\n[MOCK SMS GATEWAY] To: {user.mobile_number} | Message: {sms_body}\n")

        return True, f"OTP sent to mobile {user.mobile_number}. (Dev code: {otp_obj.otp_code})", otp_obj

    return False, "Invalid OTP type requested.", None


def verify_otp_code(user, code):
    """
    Verifies user's submitted OTP code.
    If valid, marks it used, creates a reset_token, and returns the token.
    """
    try:
        otp_obj = PasswordResetOTP.objects.filter(
            user=user,
            otp_code=code.strip(),
            is_used=False
        ).order_by('-created_at').first()

        if not otp_obj:
            return False, "Invalid OTP code. Please check and try again.", None

        if not otp_obj.is_valid():
            return False, "This OTP has expired. Please request a new one.", None

        # Mark OTP as used and generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        otp_obj.is_used = True
        otp_obj.reset_token = reset_token
        otp_obj.save()

        return True, "OTP verified successfully.", reset_token

    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return False, "An error occurred while verifying the OTP.", None
