from django import forms
from django.contrib.auth import authenticate
from .models import StudentUser


class StudentRegistrationForm(forms.ModelForm):
    """
    Form for new student registration with all required fields.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a strong password (min 6 characters)',
        }),
        min_length=6,
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
        }),
        label="Confirm Password"
    )

    class Meta:
        model = StudentUser
        fields = ['name', 'semester', 'roll_number', 'branch', 'email', 'mobile_number', 'profile_pic', 'bio']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. John Doe'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 22CS101'}),
            'branch': forms.Select(attrs={'class': 'form-input'}),
            'semester': forms.Select(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'john@example.com'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 9876543210'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Tell us about your interests in the club'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-input-file'}),
        }

    def clean_roll_number(self):
        roll = self.cleaned_data.get('roll_number', '').strip().upper()
        if StudentUser.objects.filter(roll_number__iexact=roll).exists():
            raise forms.ValidationError("A student with this Roll Number is already registered.")
        return roll

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if StudentUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this Email already exists.")
        return email

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number', '').strip()
        # Clean non-digits
        digits = ''.join(filter(str.isdigit, mobile))
        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Please enter a valid 10-digit mobile number.")
        if StudentUser.objects.filter(mobile_number=digits).exists():
            raise forms.ValidationError("An account with this Mobile Number is already registered.")
        return digits

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class StudentLoginForm(forms.Form):
    """
    Login form authenticating via Email and Password.
    """
    email = forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com', 'autocomplete': 'email'})
    email = forms.CharField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your registered email',
            'autocomplete': 'email'
        }),
        label="Email Address"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        }),
        label="Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').strip().lower()
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                # Also try looking up case-insensitively
                try:
                    matched_user = StudentUser.objects.get(email__iexact=email)
                    user = authenticate(username=matched_user.email, password=password)
                except StudentUser.DoesNotExist:
                    user = None

            if not user:
                raise forms.ValidationError("Invalid email or password. Please check your credentials.")
            if not user.is_active:
                raise forms.ValidationError("This account has been disabled. Please contact the club administrator.")
            cleaned_data['user'] = user

        return cleaned_data


class StudentProfileUpdateForm(forms.ModelForm):
    """
    Form allowing students to update their profile picture, bio, semester, mobile, and branch.
    """
    class Meta:
        model = StudentUser
        fields = ['name', 'profile_pic', 'bio', 'semester', 'branch', 'mobile_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'semester': forms.Select(attrs={'class': 'form-input'}),
            'branch': forms.Select(attrs={'class': 'form-input'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-input-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_pk = self.instance.pk if self.instance else None

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number', '').strip()
        digits = ''.join(filter(str.isdigit, mobile))
        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Please enter a valid 10-digit mobile number.")
        qs = StudentUser.objects.filter(mobile_number=digits)
        if self.instance_pk:
            qs = qs.exclude(pk=self.instance_pk)
        if qs.exists():
            raise forms.ValidationError("This mobile number is already used by another member.")
        return digits


class ForgotPasswordRequestForm(forms.Form):
    """
    Step 1: Input Email or Mobile to receive OTP.
    """
    METHOD_CHOICES = [
        ('email', 'Send OTP to Email'),
        ('mobile', 'Send OTP to Mobile Number'),
    ]

    identifier = forms.CharField(
        label="Email or Mobile Number",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your registered email or 10-digit mobile number'
        })
    )
    otp_method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
        initial='email',
        label="OTP Channel"
    )

    def clean(self):
        cleaned_data = super().clean()
        ident = cleaned_data.get('identifier', '').strip()
        method = cleaned_data.get('otp_method')

        if not ident:
            return cleaned_data

        user = None
        # Check by email
        if '@' in ident:
            user = StudentUser.objects.filter(email__iexact=ident).first()
        else:
            # Check by mobile or roll number
            digits = ''.join(filter(str.isdigit, ident))
            user = StudentUser.objects.filter(mobile_number=digits).first()
            if not user:
                user = StudentUser.objects.filter(roll_number__iexact=ident).first()

        if not user:
            raise forms.ValidationError("No registered student account was found matching this identifier.")

        if method == 'email' and not user.email:
            raise forms.ValidationError("This account does not have a valid email configured.")
        if method == 'mobile' and not user.mobile_number:
            raise forms.ValidationError("This account does not have a registered mobile number.")

        cleaned_data['user'] = user
        return cleaned_data


class VerifyOTPForm(forms.Form):
    """
    Step 2: Enter the 6-digit OTP code received.
    """
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label="6-Digit OTP Code",
        widget=forms.TextInput(attrs={
            'class': 'form-input text-center text-2xl tracking-widest font-mono',
            'placeholder': '••••••',
            'maxlength': '6',
            'autocomplete': 'one-time-code',
            'autofocus': 'autofocus'
        })
    )

    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit numeric OTP.")
        return code


class ResetPasswordForm(forms.Form):
    """
    Step 3: Enter new password once OTP is verified.
    """
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your new password (min 6 characters)',
        }),
        min_length=6,
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Re-enter your new password',
        }),
        label="Confirm New Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data
