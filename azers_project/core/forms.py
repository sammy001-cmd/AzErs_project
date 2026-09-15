from django import forms
from django.contrib.auth.forms import UserCreationForm
from decimal import Decimal
from .models import User, AzersCode, Artist, Booking
from .models import Portfolio, Product, Service, Brand, Ticket
from datetime import timedelta

 



# --- Signup ---

class MemberSignupForm(UserCreationForm):
    ROLE_CHOICES = [('artist', 'Artist'), ('brand', 'Brand')]
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    azers_code = forms.CharField(max_length=20, label="AzErs Code", required=False)
    stage_name = forms.CharField(max_length=100, required=False, label="Stage name")
    brand_name = forms.CharField(max_length=150, required=False, label="Brand name")
    profile_picture = forms.ImageField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'role', 'azers_code',
            'stage_name', 'brand_name', 'profile_picture',
            'password1', 'password2'
        )

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role') or self.initial.get('role') or 'artist'
        code_text = cleaned.get('azers_code', '').strip()

        if role == 'artist':
            if not code_text:
                self.add_error('azers_code', 'Artists must provide their AzErs code.')
            else:
                try:
                    az = AzersCode.objects.get(code__iexact=code_text)
                    if az.is_claimed:
                        # Log this so you see it in your terminal
                        print(f"DEBUG: Code {code_text} is already claimed by {az.assigned_to}")
                        self.add_error('azers_code', 'This AzErs code has already been claimed.')
                    else:
                        cleaned['azers_code_obj'] = az
                except AzersCode.DoesNotExist:
                    print(f"DEBUG: Code {code_text} does not exist in DB.")
                    self.add_error('azers_code', 'AzErs code not recognized.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        cleaned = self.cleaned_data
        
        user.email = cleaned.get('email')
        # Ensure role is set even if hidden field was missing from POST
        user.role = cleaned.get('role') or self.initial.get('role') or 'artist'
        user.is_approved = False

        if commit:
            user.save()
            if user.role == 'artist':
                az = cleaned.get('azers_code_obj')
                if az:
                    az.is_claimed = True
                    az.assigned_to = user
                    az.save()
                
                # update_or_create is good, but let's ensure defaults are safe
                Artist.objects.update_or_create(
                    user=user,
                    defaults={
                        'stage_name': cleaned.get('stage_name') or user.username,
                        'profile_picture': cleaned.get('profile_picture'),
                    }
                )
            elif user.role == 'brand':
                Brand.objects.update_or_create(
                    user=user,
                    defaults={
                        'brand_name': cleaned.get('brand_name') or user.username,
                        'profile_picture': cleaned.get('profile_picture')
                    }
                )
        return user



# --- Booking ---

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["customer_name", "customer_email", "event_date", "notes", "amount_paid"]

    def clean_amount_paid(self):
        amount_paid = self.cleaned_data.get("amount_paid")
        if amount_paid and amount_paid < 0:
            raise forms.ValidationError("Amount paid cannot be negative.")
        return amount_paid



# --- Artist Profile ---
class ArtistProfileForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ["stage_name", "genre", "bio", "profile_picture"]


# --- Seller Profile ---
# class SellerProfileForm(forms.ModelForm):
#     class Meta:
#         model = Seller
#         fields = ["business_name", "bio", "profile_picture"]


class ArtistSignupForm(MemberSignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force the initial value to 'artist' so clean() knows which rules to apply
        self.fields['role'].initial = 'artist'
        self.fields['role'].required = False
        self.fields['role'].widget = forms.HiddenInput()

    def save(self, commit=True):
        # Do NOT call super().save(commit=False) and then user.save() manually here.
        # Just let the parent (MemberSignupForm) handle the whole process.
        return super().save(commit=commit)

class BrandSignupForm(MemberSignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)                               
        # Ensure role is hidden and defaults to brand
        self.fields['role'].widget = forms.HiddenInput()
        self.fields['role'].initial = 'brand'
        self.fields['role'].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'brand' # Explicitly force the role
        if commit:
            user.save()
            # The MemberSignupForm.save() already handles 
            # Brand.objects.create(), so we don't need to repeat it here.
        return user






class BrandProfileForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ["brand_name", "website", "phone", "bank_name", "account_number", "address", "bio", "profile_picture"]
        widgets = {
            'whatsapp_number': forms.TextInput(attrs={
                'placeholder': 'e.g. 2348012345678',
                'class': 'w-full bg-gray-50 border border-gray-100 rounded-xl py-3 px-4'
            }),
        }
        help_texts = {
            'whatsapp_number': 'Include country code without the + sign (e.g., 234 for Nigeria).',
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "slug", "description", "price", "stock", "image"]

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["title", "description", "price", "duration"]



class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ["description", "file", "media_type"]

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock', 'category', 'image', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-gray-50 border border-gray-100 rounded-2xl py-4 px-6 focus:outline-none focus:ring-2 focus:ring-[#d4af37]/20 transition-all',
                'placeholder': 'Product Name'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-50 border border-gray-100 rounded-2xl py-4 px-6 focus:outline-none focus:ring-2 focus:ring-[#d4af37]/20 transition-all',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-50 border border-gray-100 rounded-2xl py-4 px-6 focus:outline-none focus:ring-2 focus:ring-[#d4af37]/20 transition-all',
                'placeholder': 'Available quantity'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full bg-gray-50 border border-gray-100 rounded-2xl py-4 px-6 focus:outline-none focus:ring-2 focus:ring-[#d4af37]/20 transition-all',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-50 border border-gray-100 rounded-2xl py-4 px-6 focus:outline-none focus:ring-2 focus:ring-[#d4af37]/20 transition-all',
                'placeholder': 'Describe the item...',
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden', # We will style a custom upload button
                'id': 'image-upload'
            }),
        }

class ServiceForm(forms.ModelForm):
    # We change the duration field to an IntegerField in the UI
    duration = forms.IntegerField(
        help_text="Enter duration in minutes (e.g., 60 for 1 hour)",
        widget=forms.NumberInput(attrs={'placeholder': 'E.g. 60'})
    )

    class Meta:
        model = Service
        fields = ['title', 'description', 'price', 'duration'       ]

    def clean_duration(self):
        minutes = self.cleaned_data.get('duration')
        # Convert the integer minutes back into a timedelta for the database
        return timedelta(minutes=minutes)
    

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['event_name', 'description', 'price', 'event_date', 'total_capacity', 'requires_photo']
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell the squad about the event...'}),
            'event_name': forms.TextInput(attrs={'placeholder': 'e.g. Azers Night Live'}),
        }
