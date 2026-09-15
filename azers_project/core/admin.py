from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, AzersCode, Artist, Booking, Brand
from django.core.mail import send_mail

from django.contrib import admin
from .models import Brand, BrandInquiry, Conversation, ChatMessage



# Custom User Admin
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active","is_approved", "date_joined")
    search_fields = ("username", "email")
    list_filter = ("role", "is_staff", "is_active", "is_approved")
    ordering = ("-date_joined",)
    list_editable = ("is_approved",)
    actions = ["approve_selected"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Approval & Role", {"fields": ("role", "is_approved")}),
    )

    def approve_selected(self, request, queryset):
        count = 0
        for user in queryset:
            if not user.is_approved:
                user.is_approved = True
                user.save()
                # send a simple email notification
                if user.email:
                    send_mail(
                        "Azers Squad — Account Approved",
                        f"Hi {user.username},\n\nYour account has been approved. You can now login to Azers Squad.",
                        None,  # uses DEFAULT_FROM_EMAIL
                        [user.email],
                        fail_silently=True,
                    )
                count += 1
        self.message_user(request, f"{count} user(s) approved and notified.")
    approve_selected.short_description = "Approve selected users and notify"




# Prevent double registration of User
try:
    admin.site.register(User, UserAdmin)
except admin.sites.AlreadyRegistered:
    pass


@admin.register(AzersCode)
class AzersCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "is_claimed", "assigned_to", "note")
    list_filter = ("is_claimed",)
    search_fields = ("code",)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("stage_name", "genre", "price_tag", "profile_picture_preview")
    search_fields = ("stage_name", "genre")
    list_filter = ("genre",)

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:5px;" />',
                obj.profile_picture.url,
            )
        return "No image"
    profile_picture_preview.short_description = "Profile Picture"


# @admin.register(Seller)
# class SellerAdmin(admin.ModelAdmin):
#     list_display = ("business_name", "user", "created_at", "profile_picture_preview")
#     search_fields = ("business_name", "user__username")
#     list_filter = ("created_at",)

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:5px;" />',
                obj.profile_picture.url,
            )
        return "No image"
    profile_picture_preview.short_description = "Profile Picture"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("artist", "customer_name", "event_date", "payment_status", "amount_paid")
    list_filter = ("payment_status", "event_date")
    search_fields = ("artist__stage_name", "customer_name")

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "user", "website", "phone", "address")
    search_fields = ("brand_name", "user__username", "website", "phone")
    list_filter = ("created_at",)



@admin.register(BrandInquiry)
class BrandInquiryAdmin(admin.ModelAdmin):
    # What columns to show in the list view
    list_display = ('sender', 'brand', 'created_at', 'is_read')
    
    # Add filters on the right side
    list_filter = ('is_read', 'created_at', 'brand')
    
    # Add a search bar to find specific users or messages
    search_fields = ('sender__username', 'brand__brand_name', 'message')
    
    # Make the date hierarchy clickable at the top
    date_hierarchy = 'created_at'
    
    # Custom action to mark multiple messages as read at once
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected inquiries as read"


# Basic registration
admin.site.register(Conversation)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    # This makes the list view much more useful
    list_display = ('sender', 'conversation', 'text', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_from_guest', 'is_read')
    search_fields = ('text', 'sender__username')


from django.contrib import admin
from .models import Ticket, TicketPurchase

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'brand', 'price', 'event_date', 'total_capacity')
    list_filter = ('brand', 'event_date')
    search_fields = ('event_name', 'brand__brand_name')
    # This allows you to edit the price and capacity directly from the list view
    list_editable = ('price', 'total_capacity')

@admin.register(TicketPurchase)
class TicketPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'email', 'ticket', 'status', 'created_at')
    list_filter = ('status', 'ticket__brand', 'created_at')
    search_fields = ('user_name', 'email', 'issued_pass_id')
    readonly_fields = ('created_at', 'issued_pass_id')
    
    # This organizes the details when you click into a purchase
    fieldsets = (
        ('Attendee Info', {
            'fields': ('user_name', 'email', 'user_photo')
        }),
        ('Event & Payment', {
            'fields': ('ticket', 'payment_receipt', 'status')
        }),
        ('System Details', {
            'fields': ('issued_pass_id', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Optional: If you approve a ticket via admin, this ensures
        a serial number is generated if it doesn't have one.
        """
        if obj.status == 'approved' and not obj.issued_pass_id:
            obj.issued_pass_id = f"AZR-{obj.ticket.id}-{obj.id}"
        super().save_model(request, obj, form, change)