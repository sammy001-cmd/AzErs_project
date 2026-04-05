from django.db import models
import uuid
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


# -------------------------
# Custom User model
# -------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('artist', 'Artist'),
        ('brand', 'Brand'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    azers_code = models.CharField(max_length=20, blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# -------------------------
# Azers Code model
# -------------------------
class AzersCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    is_claimed = models.BooleanField(default=False)
    assigned_to = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.code


# -------------------------
# Base Profile (abstract)
# -------------------------
class BaseProfile(models.Model):
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


# -------------------------
# Artist model
# -------------------------
class Artist(BaseProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stage_name = models.CharField(max_length=100)
    genre = models.CharField(max_length=100, blank=True)
    price_tag = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.stage_name or self.user.username


# -------------------------
# Portfolio model
# -------------------------
class Portfolio(models.Model):
    MEDIA_TYPES = (
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("document", "Document"),
    )
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    description = models.TextField()
    file = models.FileField(upload_to="portfolios/", blank=True, null=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES, default="image")

    def __str__(self):
        return f"{self.artist.stage_name} Portfolio"
    
    @property
    def is_image(self):
        return self.media_type == "image"



# -------------------------
# Booking model
# -------------------------
class Booking(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending Approval"),
        ("Accepted", "Accepted & Active"),
        ("Declined", "Declined"),
        ("Completed", "Gig Finished"),
        ("Cancelled", "Cancelled"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("Unpaid", "Unpaid"),
        ("Partially Paid", "Partially Paid (50%)"),
        ("Paid", "Fully Paid"),
    )

    # Core Relations
    artist = models.ForeignKey('Artist', on_delete=models.CASCADE, related_name="bookings")
    
    # Secret ID for Guest Access (Non-Guessable URL)
    secret_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Client Info
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    event_date = models.DateField()
    event_location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True, help_text="Event details, duration, etc.")
    
    # Financials
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_quote = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Workflow States
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Unpaid")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_name} -> {self.artist.stage_name} ({self.event_date})"

    def get_absolute_url(self):
        # The URL sent to the fan's email
        return reverse('core:guest_booking_detail', kwargs={'secret_id': self.secret_id})

    @property
    def balance_due(self):
        return self.total_quote - self.amount_paid

    def update_payment_logic(self):
        """Auto-calculate payment status based on amounts"""
        if self.amount_paid >= self.total_quote and self.total_quote > 0:
            self.payment_status = "Paid"
        elif self.amount_paid > 0:
            self.payment_status = "Partially Paid"
        else:
            self.payment_status = "Unpaid"
        self.save()


# class Booking(models.Model):
#     PAYMENT_STATUS_CHOICES = (
#         ("Pending", "Pending"),
#         ("Partially Paid", "Partially Paid"),
#         ("Paid", "Paid"),
#     )

#     artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
#     customer_name = models.CharField(max_length=100)
#     customer_email = models.EmailField()
#     event_date = models.DateField()
#     notes = models.TextField(blank=True)
#     amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Booking for {self.artist.stage_name} by {self.customer_name}"

#     def is_half_paid(self):
#         return self.amount_paid >= (self.artist.price_tag / 2)



# class Seller(BaseProfile):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     business_name = models.CharField(max_length=150, blank=True)

#     def __str__(self):
        
#         return self.business_name or self.user.username


class Brand(BaseProfile):
    """
    Replaces the old Seller model conceptually.
    Stores profile for brands (which can sell products and/or offer services).
    """
    user = models.OneToOneField("User", on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=150, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to="brands/", blank=True, null=True)

    @property
    def display_picture(self):
        if self.profile_picture:
            return self.profile_picture.url
        return "/static/images/default-brand.png"
    
    @property
    def whatsapp_number(self):
        """Cleans the phone number for WhatsApp API (removes +, spaces, and handles 0 prefix)"""
        if not self.phone:
            return None
        # Remove any spaces or plus signs
        clean_number = self.phone.replace(" ", "").replace("+", "")
        # If it starts with 0, replace it with Nigerian country code 234
        if clean_number.startswith('0'):
            return "234" + clean_number[1:]
        return clean_number

    def __str__(self):
        return self.brand_name or self.user.username

class Product(models.Model):
    CATEGORY_CHOICES = (
        ('fashion', 'Fashion'),
        ('electronics', 'Electronics'),
        ('beauty', 'Beauty & Health'),
        ('art', 'Art & Collectibles'),
        ('other', 'Other'),
    )
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')

    @property
    def display_image(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return "/static/images/default-product.png"
    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

class Service(models.Model):
    CATEGORY_CHOICES = (
        ('music', 'Music Production'),
        ('graphics', 'Graphic Design'),
        ('marketing', 'Marketing'),
        ('event', 'Event Planning'),
        ('other', 'Other'),
    )


    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="services")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)  # optional estimated duration
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'artist':
            Artist.objects.get_or_create(user=instance, stage_name=instance.username)
        elif instance.role == 'brand':
            Brand.objects.get_or_create(user=instance, brand_name=f"{instance.username}'s Brand")




class BrandInquiry(models.Model):
    # Who sent it (Talent or Public User)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_inquiries")
    
    # Which Brand are they contacting?
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, related_name="received_inquiries")
    
    # The actual message
    message = models.TextField()
    
    # Meta info
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Brand Inquiries"

    def __str__(self):
        return f"Inquiry from {self.sender.username} to {self.brand.brand_name}"
    
class Lead(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='leads')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead for {self.brand.brand_name} at {self.created_at}"