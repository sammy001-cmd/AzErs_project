# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import User, Artist, Brand


@receiver(post_save, sender=User)
def notify_user_approval(sender, instance, created, **kwargs):
    # Only trigger when user is updated, not when first created
    if not created and instance.is_approved:
        send_mail(
            "Account Approved ",
            f"Hello {instance.username}, your account has been approved by the admin. "
            "You can now log in and access your dashboard.",
            "no-reply@Azersquad.com",   # Replace with your sender email
            [instance.email],
            fail_silently=True,
        )
def create_role_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'artist' and not hasattr(instance, 'artist'):
            Artist.objects.create(user=instance, stage_name=instance.username, price_tag=0)
        elif instance.role == 'brand' and not hasattr(instance, 'brand'):
            Brand.objects.create(user=instance, brand_name=instance.username)