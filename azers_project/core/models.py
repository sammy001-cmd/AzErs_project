from django.db import models
import uuid
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from cloudinary.models import CloudinaryField
from .storage import PortfolioCloudinaryStorage


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
    profile_picture = CloudinaryField("image", folder="profiles", blank=True, null=True)
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

    @property
    def display_picture(self):
        if self.profile_picture:
            if hasattr(self.profile_picture, 'url'):
                return self.profile_picture.url
            return str(self.profile_picture)
        return "/static/images/default-artist.png"

    def __str__(self):
        return self.stage_name or self.user.username


def portfolio_upload_path(instance, filename):
    return f"portfolios/{instance.media_type}/{filename}"


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
    file = models.FileField(
        upload_to=portfolio_upload_path,
        storage=PortfolioCloudinaryStorage(),
        blank=True,
        null=True,
    )
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES, default="image")

    def __str__(self):
        return f"{self.artist.stage_name} Portfolio"
    
    @property
    def is_image(self):
        return self.media_type == "image"







class Brand(BaseProfile):
    """
    Replaces the old Seller model conceptually.
    Stores profile for brands (which can sell products and/or offer services).
    """
    user = models.OneToOneField("User", on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=150, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    profile_picture = CloudinaryField("image", folder="brands", blank=True, null=True)

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
    image = CloudinaryField("image", folder="products", blank=True, null=True)
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
    STATUS_CHOICES = [
        ('new', 'New'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]
    # Who sent it (Talent or Public User)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_inquiries")
    
    # Which Brand are they contacting?
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, related_name="received_inquiries")
    
    # The actual message
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
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
    

class Conversation(models.Model):
    # For registered Brands/Users chatting with Artists
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations", blank=True)
    
    # The Professional (Artist or Brand) who "owns" this chat channel
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="managed_chats")
    
    # Guest Access Logic (The "Secret Link" feature)
    is_guest_chat = models.BooleanField(default=False)
    guest_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guest_name = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subject_type = models.CharField(max_length=100, blank=True, null=True)
    visitor_email = models.EmailField(blank=True, null=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat for {self.receiver.username} (Guest: {self.is_guest_chat})"

class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    # sender is NULL if a guest is sending the message
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    # Explicitly track guest messages
    is_from_guest = models.BooleanField(default=False)
    image = CloudinaryField("image", folder="chat_images", blank=True, null=True)
    text = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']


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

    # --- THE LINK TO THE CHAT ---
    # Every booking now HAS a chat room. 
    conversation = models.OneToOneField(
        Conversation,   
        on_delete=models.CASCADE, 
        related_name="booking",
        help_text="The chat room dedicated to this specific booking",
        null=True,
        blank=True
       )

    artist = models.ForeignKey('Artist', on_delete=models.CASCADE, related_name="bookings")
    
    # Client Info (copied from conversation if guest)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    event_date = models.DateField()
    event_location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    # Financials (Negotiable inside the chat!)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_quote = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Unpaid")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking: {self.customer_name} -> {self.artist.stage_name}"
    

class Ticket(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="tickets")
    event_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Ticket Specifics
    event_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, help_text="Physical or Virtual Link")
    total_capacity = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    
    # The "Cool" Factor
    requires_photo = models.BooleanField(default=True, help_text="If true, users must upload a photo for the digital pass")
    ticket_template = CloudinaryField("image", folder="tickets/templates", blank=True, null=True, help_text="The blank design we will paste the user face onto")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-event_date",)

    def __str__(self):
        return f"{self.event_name} - {self.brand.brand_name}"
    
    
class TicketPurchase(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="purchases")
    user_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    user_photo = CloudinaryField("image", folder="ticket_holders")
    payment_receipt = CloudinaryField("image", folder="payment_proofs")
    status = models.CharField(max_length=20, default="pending", choices=[
        ('pending', 'Verifying'),
        ('approved', 'Issued'),
        ('declined', 'Failed')
    ])
    issued_pass_id = models.CharField(max_length=50, blank=True) # e.g. AZR-WEB-001
