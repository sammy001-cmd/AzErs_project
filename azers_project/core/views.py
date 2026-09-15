from decimal import Decimal, InvalidOperation
import email
from django.core.paginator import Paginator
# from os import name
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.urls import reverse
from .models import Portfolio
from .forms import ArtistProfileForm, PortfolioForm
from .models import Artist, Booking, Conversation, ChatMessage, Ticket, TicketPurchase
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .models import Portfolio, Brand, Product, Service, BrandInquiry,Lead
from .forms import PortfolioForm, BrandProfileForm, ProductForm, ServiceForm
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import Sum
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
import requests
from django.db import transaction
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from .forms import TicketForm
import logging
from smtplib import SMTPException









from .forms import (
    MemberSignupForm,
    ArtistSignupForm,
    BrandSignupForm,
    BookingForm,
    ArtistProfileForm,
)

# --- Public ---
def home(request):
    featured_artists = Artist.objects.filter(user__is_approved=True).order_by('-created_at')[:6]
    featured_brands = Brand.objects.filter(user__is_approved=True).order_by('-created_at')[:6]
    # print("DEBUG Featured brands:", featured_brands)  # <-- check console
    return render(request, "core/home.html", {
        "featured_artists": featured_artists,
        "featured_brands": featured_brands,
        "total_artists": Artist.objects.filter(user__is_approved=True).count(),
        "total_brands": Brand.objects.filter(user__is_approved=True).count(),
        "total_bookings": Booking.objects.filter(status="Accepted").count(),
    })

# def home(request):
#     featured_artists = Artist.objects.filter(user__is_approved=True).order_by('-created_at')[:6]
#     featured_brands = Brand.objects.filter(user__is_approved=True).order_by('-created_at')[:6]
#     return render(request, "core/home.html", {
#         "featured_artists": featured_artists,
#         "featured_brands": featured_brands,
#     })




def artist_list(request):
    search_query = request.GET.get('search', '')
    genre_query = request.GET.get('genre', '')
    
    artists = Artist.objects.filter(user__is_approved=True).order_by('-created_at')
    
    if search_query:
        artists = artists.filter(stage_name__icontains=search_query)
    if genre_query:
        artists = artists.filter(genre__icontains=genre_query)
    
    paginator = Paginator(artists, 12)
    page_number = request.GET.get('page')
    artists = paginator.get_page(page_number)
    
    return render(request, "core/artist_list.html", {
        "artists": artists,
        "search_query": search_query,
        "genre_query": genre_query,
    })

def brand_list(request):
    search_query = request.GET.get('search', '')
    
    brands = Brand.objects.filter(user__is_approved=True).order_by('-created_at')
    
    if search_query:
        brands = brands.filter(brand_name__icontains=search_query)
    
    paginator = Paginator(brands, 12)
    page_number = request.GET.get('page')
    brands = paginator.get_page(page_number)
    
    return render(request, "core/brand_list.html", {
        "brands": brands,
        "search_query": search_query,
    })


def artist_detail(request, pk):
    artist = get_object_or_404(Artist, pk=pk)
    return render(request, "core/artist_detail.html", {"artist": artist})


# def seller_detail(request, seller_id):
#     seller = get_object_or_404(Seller, id=seller_id)
#     return render(request, "core/seller_detail.html", {"seller": seller})



# @login_required
# def book_artist(request, artist_id):
#     artist = get_object_or_404(Artist, id=artist_id)
#     if request.method == "POST":
#         form = BookingForm(request.POST)
#         if form.is_valid():
#             booking = form.save(commit=False)
#             # Ensure we compare Decimals
#             min_upfront = (artist.price_tag / Decimal("2"))
#             if booking.amount_paid < min_upfront:
#                 # show a helpful error on the form field
#                 form.add_error(
#                     "amount_paid",
#                     f"At least 50% upfront is required (minimum ₦{min_upfront})."
#                 )
#             else:
#                 booking.artist = artist
#                 # optionally: booking.customer = request.user  (if your Booking model has a customer/user field)
#                 booking.save()
#                 messages.success(request, "Booking submitted. Await confirmation.")
#                 return redirect("booking_list")  # keep your existing url name
#     else:
#         form = BookingForm()
#     return render(request, "core/book_artist.html", {"form": form, "artist": artist})



# @login_required
# def booking_list(request):
#     bookings = Booking.objects.filter(customer_email=request.user.email)
#     return render(request, "core/booking_list.html", {"bookings": bookings})



# --- Artist Dashboard ---

@login_required
def artist_dashboard(request):
    if request.user.role != 'artist':
        return HttpResponseForbidden("Only artists can access this.")
    
    # Get or create artist profile
    artist, created = Artist.objects.get_or_create(
        user=request.user, 
        defaults={'stage_name': request.user.username}
    )

    # Calculate revenue
    total_revenue = artist.bookings.filter(
        payment_status__in=["Paid", "Partially Paid"]
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0.00
    
    # Get bookings: Newest first
    bookings = artist.bookings.all().order_by('-id')
    pending_count = bookings.filter(status='Pending').count()
    confirmed_count = bookings.filter(status='Accepted').count()
    
    context = {
        "artist": artist, 
        "total_revenue": total_revenue,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        "bookings": bookings
    }
    return render(request, "core/artist_dashboard.html", context)


@login_required
def edit_artist_profile(request):
    if request.user.role != 'artist':
        return HttpResponseForbidden("Only artists can edit.")
    artist = get_object_or_404(Artist, user=request.user)
    if request.method == "POST":
        form = ArtistProfileForm(request.POST, instance=artist)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("core:artist_dashboard")
    else:
        form = ArtistProfileForm(instance=artist)
    return render(request, "core/edit_artist_profile.html", {"form": form})


# --- Seller Dashboard ---
# @login_required
# def seller_dashboard(request):
#     if request.user.role != 'seller':
#         return HttpResponseForbidden("Only sellers can access this.")
#     seller = get_object_or_404(Seller, user=request.user)
#     return render(request, "core/seller_dashboard.html", {"seller": seller})


# @login_required
# def edit_seller_profile(request):
#     if request.user.role != 'seller':
#         return HttpResponseForbidden("Only sellers can edit.")
#     seller = get_object_or_404(Seller, user=request.user)
#     if request.method == "POST":
#         form = SellerProfileForm(request.POST, request.FILES, instance=seller)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Seller profile updated.")
#             return redirect("core:seller_dashboard")
#     else:
#         form = SellerProfileForm(instance=seller)
#     return render(request, "core/edit_seller_profile.html", {"form": form})

def member_signup(request):
    return render(request, "core/member_signup.html")


def artist_signup(request):
    if request.method == "POST":
        print(f"FILES received: {request.FILES}") # <--- Look at your terminal!
        form = ArtistSignupForm(request.POST, request.FILES) # FILES is key for the image
        if form.is_valid():
            form.save() 
            messages.success(request, "Registration successful! Await admin approval.")
            return redirect("core:home")
        else:
            # print(f"Form Errors: {.errors}") # <--- This tells you the truth
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ArtistSignupForm()
    return render(request, "core/artist_signup.html", {"form": form})


def brand_signup(request):
    if request.method == "POST":
        form = BrandSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'brand'
            user.is_approved = False
            user.save()  # This might trigger a signal to create the Brand
            
            # Use update_or_create to avoid the UNIQUE constraint error
            Brand.objects.update_or_create(
                user=user, 
                defaults={
                    'brand_name': getattr(user, 'username') + "'s Brand"
                }
            )
            
            messages.success(request, "Submitted successfully. Await admin approval.")
            return redirect("core:home")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BrandSignupForm()
    return render(request, "core/brand_signup.html", {"form": form})



def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_approved and not user.is_staff :
                return redirect("core:awaiting_approval")
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            # Redirect based on role
            if user.is_staff:  
                return redirect("core:admin_dashboard") 
            elif user.role == "artist":
                return redirect("core:artist_dashboard")
            elif user.role == "brand":
                return redirect("core:brand_dashboard")
            else:
                return redirect("core:home")
    else:
        form = AuthenticationForm()
    return render(request, "core/login.html", {"form": form})



# --- Portfolio management ---
@login_required
def portfolio_list(request):
    if request.user.role != 'artist':
        return HttpResponseForbidden("Only artists can access this.")
    artist = get_object_or_404(Artist, user=request.user)
    portfolios = Portfolio.objects.filter(artist=artist)
    return render(request, "core/portfolio_list.html", {"artist": artist, "portfolios": portfolios})


@login_required
def add_portfolio_item(request):
    if request.user.role != 'artist':
        return HttpResponseForbidden("Only artists can access this.")
    artist = get_object_or_404(Artist, user=request.user)
    
    if request.method == "POST":
        form = PortfolioForm(request.POST, request.FILES)
        if form.is_valid():
            portfolio_item = form.save(commit=False)
            portfolio_item.artist = artist
            portfolio_item.save()
            messages.success(request, "Portfolio item added successfully.")
            return redirect("core:portfolio_list")
    else:
        form = PortfolioForm()
    
    return render(request, "core/add_portfolio_item.html", {"form": form})


@login_required
def delete_portfolio_item(request, item_id):
    if request.user.role != 'artist':
        return HttpResponseForbidden("Only artists can access this.")
    item = get_object_or_404(Portfolio, id=item_id, artist__user=request.user)
    item.delete()
    messages.success(request, "Portfolio item deleted.")
    return redirect("core:portfolio_list")


def awaiting_approval(request):
    return render(request, "core/awaiting_approval.html")



@login_required
@login_required
def brand_dashboard(request):
    brand = get_object_or_404(Brand, user=request.user)
    products = Product.objects.filter(brand=brand).order_by('-created_at')
    services = Service.objects.filter(brand=brand).order_by('-created_at')
    brand_chats = (
        Conversation.objects.filter(receiver=request.user)
        .prefetch_related("participants")
        .order_by("-updated_at")[:8]
    )
    
    return render(request, "core/brand_dashboard.html", {
        "brand": brand,
        "products": products,
        "services": services,
        "brand_chats": brand_chats,
    })


def brand_detail(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    search_query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "newest").strip()
    per_page = request.GET.get("per_page", "12").strip()

    allowed_per_page = {"8", "12", "24", "36"}
    if per_page not in allowed_per_page:
        per_page = "12"

    products_qs = brand.products.all()

    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    valid_categories = {choice[0] for choice in Product.CATEGORY_CHOICES}
    if category and category in valid_categories:
        products_qs = products_qs.filter(category=category)
    else:
        category = ""

    sort_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "name_asc": "name",
        "name_desc": "-name",
    }
    if sort not in sort_map:
        sort = "newest"
    products_qs = products_qs.order_by(sort_map[sort], "-id")

    paginator = Paginator(products_qs, int(per_page))
    products_page = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    preserved_query = query_params.urlencode()

    return render(
        request,
        "core/brand_detail.html",
        {
            "brand": brand,
            "products_page": products_page,
            "products_total": products_qs.count(),
            "search_query": search_query,
            "selected_category": category,
            "selected_sort": sort,
            "selected_per_page": per_page,
            "category_choices": Product.CATEGORY_CHOICES,
            "preserved_query": preserved_query,
        },
    )

@login_required
def edit_brand_profile(request):
    brand = get_object_or_404(Brand, user=request.user) # Make sure this is passed!
    if request.user.role not in ("brand", "seller"):
        return HttpResponseForbidden("Only brands can edit this.")
    brand = get_object_or_404(Brand, user=request.user)
    if request.method == "POST":
        form = BrandProfileForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand profile updated.")
            return redirect("core:brand_dashboard")
    else:
        form = BrandProfileForm(instance=brand)
    return render(request, "core/edit_brand_profile.html", {"form": form, "brand": brand})


def send_inquiry(request, brand_id):  # <--- Make sure this is 'send_inquiry'
    brand = get_object_or_404(Brand, id=brand_id)
    
    if request.method == "POST":
        message_text = request.POST.get('message')
        
        # Save to database
        BrandInquiry.objects.create(
            sender=request.user,
            brand=brand,
            message=message_text
        )
        
        messages.success(request, f"Your inquiry has been sent to {brand.brand_name}!")
        return redirect('core:brand_detail', pk=brand.id)

    # This part handles the GET request (showing the page)
    return render(request, 'core/brand_public.html', {'brand': brand})

# Product CRUD
@login_required
def add_product(request):
    if request.user.role not in ("brand", "seller"):
        return HttpResponseForbidden("Only brands can add products.")
    brand = get_object_or_404(Brand, user=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.brand = brand
            p.save()
            messages.success(request, "Product added.")
            return redirect("core:brand_dashboard")
    else:
        form = ProductForm()
    return render(request, "core/product_form.html", {"form": form, "action": "Add Product"})

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, brand__user=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("core:brand_dashboard")
    else:
        form = ProductForm(instance=product)
    return render(request, "core/product_form.html", {"form": form, "action": "Edit Product"})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, brand__user=request.user)
    product.delete()
    messages.success(request, "Product deleted.")
    return redirect("core:brand_dashboard")

# Service CRUD
@login_required
def add_service(request):
    if request.user.role not in ("brand", "seller"):
        return HttpResponseForbidden("Only brands can add services.")
    brand = get_object_or_404(Brand, user=request.user)
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.brand = brand
            s.save()
            messages.success(request, "Service added.")
            return redirect("core:brand_dashboard")
    else:
        form = ServiceForm()
    return render(request, "core/service_form.html", {"form": form, "action": "Add Service"})

@login_required
def edit_service(request, pk):
    service = get_object_or_404(Service, pk=pk, brand__user=request.user)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated.")
            return redirect("core:brand_dashboard")
    else:
        form = ServiceForm(instance=service)
    return render(request, "core/service_form.html", {"form": form, "action": "Edit Service"})

@login_required
def delete_service(request, pk):
    service = get_object_or_404(Service, pk=pk, brand__user=request.user)
    service.delete()
    messages.success(request, "Service deleted.")
    return redirect("core:brand_dashboard")


# @login_required
# def admin_dashboard(request):
#     if not request.user.is_staff:
#         return redirect('core:home') # Keep non-admins out
        
#     context = {
#         'total_artists': User.objects.filter(role='artist').count(),
#         'total_brands': User.objects.filter(role='brand').count(),
#         'pending_users': User.objects.filter(is_approved=False).count(),
#         'recent_users': User.objects.all().order_by('-date_joined')[:15],
#     }
#     return render(request, "core/admin_dashboard.html", context)


 

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('core:home')
 
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
 
    # ── User Stats ──
    total_artists = User.objects.filter(role='artist').count()
    total_brands  = User.objects.filter(role='brand').count()
    pending_users = User.objects.filter(is_approved=False, is_staff=False).count()
    new_this_month = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    disabled_users = User.objects.filter(is_active=False, is_staff=False).count()
 
    # ── Booking Stats ──
    total_bookings    = Booking.objects.count()
    pending_bookings  = Booking.objects.filter(status='Pending').count()
    accepted_bookings = Booking.objects.filter(status='Accepted').count()
    declined_bookings = Booking.objects.filter(status='Declined').count()
 
    # ── Bookings per day (last 7 days) for chart ──
    booking_chart = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        count = Booking.objects.filter(
            id__gte=0  # replace with created_at filter if you have that field
        ).count()
        # If Booking has no created_at, just send zeros - chart still renders
        booking_chart.append({
            'day': day.strftime('%a'),
            'count': 0  # swap for real count once created_at is added
        })
 
    # ── Brand Inquiry Stats ──
    total_inquiries = BrandInquiry.objects.count()
    new_inquiries   = BrandInquiry.objects.filter(
        # if you have created_at: created_at__gte=seven_days_ago
    ).count() if hasattr(BrandInquiry, 'created_at') else total_inquiries
 
    # ── Conversation / Chat Stats ──
    total_conversations = Conversation.objects.count()
    guest_conversations = Conversation.objects.filter(is_guest_chat=True).count()
    active_conversations = Conversation.objects.filter(
        booking__status='Accepted'
    ).count()
 
    # ── Feeds ──
    recent_users      = User.objects.filter(is_staff=False).order_by('-date_joined')[:25]
    recent_bookings   = Booking.objects.select_related('artist', 'artist__user').order_by('-id')[:12]
    pending_user_list = User.objects.filter(is_approved=False, is_staff=False).order_by('-date_joined')[:15]
    recent_inquiries  = BrandInquiry.objects.select_related('brand', 'sender').order_by('-id')[:8]
    all_conversations = Conversation.objects.prefetch_related('messages').order_by('-updated_at')[:15]
 
    context = {
        # User
        'total_artists': total_artists,
        'total_brands': total_brands,
        'pending_users': pending_users,
        'new_this_month': new_this_month,
        'disabled_users': disabled_users,
        # Bookings
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'accepted_bookings': accepted_bookings,
        'declined_bookings': declined_bookings,
        'booking_chart': booking_chart,
        # Inquiries
        'total_inquiries': total_inquiries,
        'recent_inquiries': recent_inquiries,
        # Conversations
        'total_conversations': total_conversations,
        'guest_conversations': guest_conversations,
        'active_conversations': active_conversations,
        'all_conversations': all_conversations,
        # Feeds
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'pending_user_list': pending_user_list,
    }
    return render(request, "core/admin_dashboard.html", context)
 
 
# ── Approve user ──
@login_required
def approve_user(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Access Denied")
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f"✓ {user.username} has been approved.")
    return redirect('core:admin_dashboard')
 
 
# ── Disable / Enable account ──
@login_required
def toggle_user_active(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Access Denied")
    user = get_object_or_404(User, id=user_id)
    if user.is_staff:
        messages.error(request, "Cannot disable a staff account.")
        return redirect('core:admin_dashboard')
    user.is_active = not user.is_active
    user.save()
    action = "enabled" if user.is_active else "disabled"
    messages.success(request, f"Account {user.username} has been {action}.")
    return redirect('core:admin_dashboard')
 
 
# ── Delete account ──
@login_required
def delete_user(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Access Denied")
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_staff:
            messages.error(request, "Cannot delete a staff account.")
            return redirect('core:admin_dashboard')
        username = user.username
        user.delete()
        messages.success(request, f"Account '{username}' has been permanently deleted.")
    return redirect('core:admin_dashboard')


def marketplace(request):
    # 1. Get queries from the URL
    category_query = request.GET.get('cat')
    search_query = request.GET.get('search')
    
    # 2. Base QuerySet: Only show products from approved users
    products = Product.objects.filter(brand__user__is_approved=True)
    brands = Brand.objects.filter(user__is_approved=True)

    # 3. Apply Search Filter (if user typed something)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(brand__brand_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # 4. Apply Category Filter (if user clicked a category)
    if category_query:
        products = products.filter(category=category_query)

    # 5. Finalize ordering
    latest_products = products.order_by('-created_at')

    # Get categories for the template ribbon
    categories = Product.CATEGORY_CHOICES 

    return render(request, "core/marketplace.html", {
        "brands": brands,
        "latest_products": latest_products,
        "categories": categories,
        "active_category": category_query,
        "search_query": search_query,
    })


from .forms import ProductForm 

@login_required
def add_product(request):
    brand = get_object_or_404(Brand, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.brand = brand # Automatically assign the brand
            product.save()
            return redirect('core:brand_dashboard')
    else:
        form = ProductForm()
    
    return render(request, 'core/add_product.html', {'form': form})


from django.http import JsonResponse

def track_lead(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Lead.objects.create(brand=product.brand, product=product)
    return JsonResponse({'status': 'tracked'})

# @login_required
# def add_service(request):
#     if request.user.role not in ("brand", "seller"):
#         return HttpResponseForbidden("Only brands can list services.")

#     # Get the brand associated with the logged-in user
#     brand = get_object_or_404(Brand, user=request.user)

#     if request.method == "POST":
#         form = ServiceForm(request.POST)
#         if form.is_valid():
#             # commit=False lets us add the brand ID before saving to the DB
#             service = form.save(commit=False)
#             service.brand = brand 
#             service.save()
            
#             messages.success(request, f"New Professional Service: {service.title} has been listed!")
#             return redirect("core:brand_dashboard")
#     else:
#         form = ServiceForm()

#     return render(request, "core/service_form.html", {
#         "form": form, 
#         "action": "Add Service",
#         "brand": brand
#     })


@login_required
def delete_product(request, pk):
    # Security check: Ensure the product belongs to the user's brand
    product = get_object_or_404(Product, pk=pk, brand__user=request.user)
    product_name = product.name
    product.delete()
    messages.success(request, f"Product '{product_name}' was deleted.")
    return redirect('core:brand_dashboard')

@login_required
def delete_service(request, pk):
    service = get_object_or_404(Service, pk=pk, brand__user=request.user)
    service_title = service.title
    service.delete()
    messages.success(request, f"Service '{service_title}' was deleted.")
    return redirect('core:brand_dashboard')



@login_required
def edit_product(request, pk):
    # Security: Ensure the user owns the brand that owns this product
    product = get_object_or_404(Product, pk=pk, brand__user=request.user)
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{product.name}' updated successfully!")
            return redirect('core:brand_dashboard')
    else:
        form = ProductForm(instance=product)
        
    return render(request, "core/edit_product.html", {
        "form": form,
        "product": product
    })



def add_service(request):
    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Save the service but don't commit to DB yet
            service = form.save(commit=False)
            
            # 2. Link it to the user's brand (Crucial!)
            # Assuming your Brand model has a 'user' field
            service.brand = request.user.brand 
            
            service.save()
            
            messages.success(request, "Service added to your collection!")
            return redirect('core:brand_dashboard') # Takes you back to see the result
        else:
            # If the form is NOT valid, this will show you why in the console
            print(form.errors) 
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceForm()
    
    return render(request, 'core/add_service.html', {'form': form})



def custom_404(request, exception):
    return render(request, 'core/404.html', status=404)

def custom_500(request):
    return render(request, 'core/500.html', status=500)

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    
    # This triggers the toast
    messages.success(request, f"Node {user.username} has been verified.")
    
    return redirect('core:admin_dashboard')


def book_artist(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        date = request.POST.get('date')
        notes = request.POST.get('notes', '')

        with transaction.atomic():
            convo = Conversation.objects.create(
                receiver=artist.user,
                is_guest_chat=not request.user.is_authenticated,
                guest_name=name if not request.user.is_authenticated else None
            )

            booking = Booking.objects.create(
                conversation=convo,
                artist=artist,
                customer_name=name,
                customer_email=email,
                event_date=date,
                total_quote=artist.price_tag,
                notes=notes,
                status="Pending" 
            )

        # EMAIL 1: Just a confirmation, NO chat link.
        try:
            send_mail(
                subject=f"Request Received: {artist.stage_name} @ Azers Squad",
                message=f"Hi {name},\n\nYour request for {artist.stage_name} has been transmitted. Please wait for the artist to review your request. You will receive a separate email with    your private chat link once they approve.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except:
            pass
        
        messages.success(request, "Request Sent! We will email you once the artist reviews it.")
        return redirect('core:home') # Redirect away from the chat
    
    return render(request, "core/booking_form.html", {"artist": artist})

# def book_artist(request, artist_id):
#     artist = get_object_or_404(Artist, id=artist_id)
    
#     if request.method == "POST":
#         name = request.POST.get('name')
#         email = request.POST.get('email')
#         date = request.POST.get('date')
        
#         # Proper Try/Except for Decimal conversion
#         try:
#             deposit_input = request.POST.get('amount', '0')
#             deposit = Decimal(deposit_input) if deposit_input else Decimal('0')
#         except (InvalidOperation, ValueError):
#             messages.error(request, "Please enter a valid numerical amount.")
#             return redirect(request.path)

#         # Premium Validation: 50% Rule
#         min_deposit = artist.price_tag / 2
#         if deposit < min_deposit:
#             messages.error(request, f"Minimum 50% deposit (₦{min_deposit}) required.")
#             return redirect(request.path)

#         # Create the Booking
#         booking = Booking.objects.create(
#             artist=artist,
#             customer_name=name,
#             customer_email=email,
#             event_date=date,
#             amount_paid=0.00,
#             total_quote=artist.price_tag,
#             notes=request.POST.get('notes', '')
#         )
#         booking.update_payment_logic()
        
#         # Build the Secret Guest URL
#         full_url = request.build_absolute_uri(booking.get_absolute_url())

#         # TRIGGER EMAIL: "Request Received"
#         send_mail(
#             subject=f"Request Sent: {artist.stage_name} @ Azers Squad",
#             message=f"Hi {name},\n\nYour booking request for {artist.stage_name} has been sent! \n\nTrack status and pay balance here: {full_url}",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[email],
#             fail_silently=False,
#         )
        
#         messages.success(request, "Request Sent! Check your email for your private tracking link.")
#         return redirect('core:guest_booking_detail', secret_id=booking.secret_id)
    
#     return render(request, "core/booking_form.html", {"artist": artist})

# 2. THE GUEST VIEW (The link fans click)
def guest_booking_detail(request, secret_id):
    booking = get_object_or_404(Booking, secret_id=secret_id)
    
    # We pull from settings.py and send it to the HTML
    context = {
        "booking": booking,
        "paystack_public_key": settings.PAYSTACK_PUBLIC_KEY 
    }
    return render(request, "core/guest_booking_detail.html", context)

# 3. THE ARTIST ACTION (Dashboard Controls)
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

@login_required
def artist_update_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, artist__user=request.user)
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "accept":
            if not settings.EMAIL_HOST_PASSWORD:
                messages.error(
                    request,
                    "Booking was not accepted because email is not configured. "
                    "Add EMAIL_HOST_PASSWORD to azers_project/.env and try again.",
                )
                return redirect('core:artist_dashboard')

            booking.status = "Accepted"
            booking.save() # Status is now 'Accepted', opening the gate
            
            # Generate the portal URL
            portal_path = reverse('core:public_chat_room', kwargs={'guest_uuid': booking.conversation.guest_uuid})
            full_url = request.build_absolute_uri(portal_path)

            # EMAIL 2: The "Golden Link"
            subject = f"APPROVED: Chat with {booking.artist.stage_name} now!"
            html_content = render_to_string('emails/booking_accepted.html', {
                'booking': booking,
                'full_url': full_url  # The link only works now
            })
            
            msg = EmailMultiAlternatives(subject, strip_tags(html_content), settings.DEFAULT_FROM_EMAIL, [booking.customer_email])
            msg.attach_alternative(html_content, "text/html")
            try:
                msg.send()
            except SMTPException:
                logger.exception("Booking accepted but approval email failed for booking_id=%s", booking.id)
                messages.error(
                    request,
                    "Booking was accepted, but Gmail could not send the approval email. "
                    "Check the Gmail app password and retry after correcting it.",
                )
                return redirect('core:artist_dashboard')

            messages.success(request, "Booking Accepted! The client now has their chat link.")
            
        elif action == "decline":
            booking.status = "Declined"
            booking.save()
            messages.warning(request, "Booking declined.")
            
    return redirect('core:artist_dashboard')




def download_booking_pdf(request, secret_id):
    booking = get_object_or_404(Booking, secret_id=secret_id)
    display_id = str(booking.secret_id)[:8].upper() 
    
    doc_title = "Official Payment Receipt" if booking.amount_paid > 0 else "Booking Invoice"

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Logo Logic
    logo_path = os.path.join(settings.BASE_DIR, 'static/images/azers_logo.png')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, (width/2) - 0.5*inch, height - 1.5*inch, width=1*inch, height=1*inch, mask='auto')

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 1.8*inch, "AZERS SQUAD")
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, height - 2.0*inch, f"{doc_title} | REF: {display_id}")

    def draw_row(label, value, y):
        p.setFont("Helvetica-Bold", 9)
        p.setFillColor(colors.grey)
        p.drawString(1*inch, y, label.upper())
        p.setFont("Helvetica", 11)
        p.setFillColor(colors.black)
        p.drawString(3*inch, y, str(value))
        return y - 0.4*inch

    # Grid Start
    y_pos = height - 2.8*inch
    y_pos = draw_row("Client", booking.customer_name, y_pos)
    y_pos = draw_row("Artist", booking.artist.stage_name, y_pos)
    y_pos = draw_row("Email", booking.customer_email, y_pos)
    y_pos = draw_row("Event Date", booking.event_date.strftime('%B %d, %Y'), y_pos)
    
    p.line(1*inch, y_pos + 0.1*inch, 7*inch, y_pos + 0.1*inch)
    y_pos -= 0.4*inch

    # Financials (Fixed Positional Arguments)
    y_pos = draw_row("Total Quote", f"NGN {booking.total_quote:,.2f}", y_pos)
    y_pos = draw_row("Amount Paid", f"NGN {booking.amount_paid:,.2f}", y_pos)
    
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.red if booking.balance_due > 0 else colors.green)
    y_pos = draw_row("Remaining Balance", f"NGN {booking.balance_due:,.2f}", y_pos)
    y_pos -= 0.2*inch

    # Instructions
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(1*inch, y_pos, "SPECIAL INSTRUCTIONS:")
    y_pos -= 0.25*inch
    
    notes = booking.notes if booking.notes else "No specific instructions provided."
    lines = simpleSplit(notes, "Helvetica-Oblique", 10, 5*inch)
    
    text_obj = p.beginText(1*inch, y_pos)
    text_obj.setFont("Helvetica-Oblique", 10)
    text_obj.setFillColor(colors.darkslategray)
    for line in lines:
        text_obj.textLine(line)
    p.drawText(text_obj)

    # Footer
    p.setFont("Helvetica-Oblique", 8)
    p.setFillColor(colors.grey)
    p.drawCentredString(width/2, 1*inch, "This is a system-generated document. Secured by Azers Squad Management 2026.")

    p.showPage()
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="AzersSquad_{display_id}.pdf"'
    return response




def verify_payment(request, secret_id):
    booking = get_object_or_404(Booking, secret_id=secret_id)
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, "Payment reference missing.")
        return redirect(booking.get_absolute_url())

    # Verify with Paystack API
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    res_data = response.json()

    if res_data['status'] and res_data['data']['status'] == 'success':
        # 1. Update the amount paid
        # Paystack returns amount in Kobo, so divide by 100
        paid_amount = res_data['data']['amount'] / 100
        booking.amount_paid += Decimal(str(paid_amount))
        
        # 2. Update status logic 
        booking.update_payment_logic() 
        booking.save()
        
        messages.success(request, f"Payment of ₦{paid_amount} confirmed! Your booking is secured.")
    else:
        messages.error(request, "Payment verification failed. Please contact support.")

    return redirect(booking.get_absolute_url())

def verify_payment(request, secret_id):
    booking = get_object_or_404(Booking, secret_id=secret_id)
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, "Payment reference missing.")
        return redirect(booking.get_absolute_url())

    # Verify with Paystack API
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    res_data = response.json()

    if res_data['status'] and res_data['data']['status'] == 'success':
        # 1. Update the amount paid
        # Paystack returns amount in Kobo, so divide by 100
        paid_amount = res_data['data']['amount'] / 100
        booking.amount_paid += Decimal(str(paid_amount))
        
        # 2. Update status logic 
        booking.update_payment_logic() 
        booking.save()
        
        messages.success(request, f"Payment of ₦{paid_amount} confirmed! Your booking is secured.")
    else:
        messages.error(request, "Payment verification failed. Please contact support.")

    return redirect(booking.get_absolute_url())




def initiate_booking_chat(request, artist_id):
    """
    This view is triggered when someone clicks 'Book' on an artist profile.
    It creates the chat room and the booking record simultaneously.
    """
    artist = get_object_or_404(Artist, id=artist_id)
    
    if request.method == "POST":
        customer_name = request.POST.get('customer_name')
        customer_email = request.POST.get('customer_email')
        event_date = request.POST.get('event_date')

        with transaction.atomic():
            # 1. Create the Conversation Room
            convo = Conversation.objects.create(
                receiver=artist.user,
                is_guest_chat=not request.user.is_authenticated,
                guest_name=customer_name if not request.user.is_authenticated else None
            )
            
            if request.user.is_authenticated:
                convo.participants.add(request.user)

            # 2. Create the Booking linked to this Room
            booking = Booking.objects.create(
                conversation=convo,
                artist=artist,
                customer_name=customer_name,
                customer_email=customer_email,
                event_date=event_date,
                total_quote=artist.price_tag
            )

        # 3. Handle Guest Session
        if not request.user.is_authenticated:
            request.session[f"guest_chat_{convo.guest_uuid}"] = True
            # Extend session to last until event date
            request.session.set_expiry(60 * 60 * 24 * 60)  # 60 days
            return redirect('core:public_chat_room', guest_uuid=convo.guest_uuid)
        
        return redirect('core:chat_room', room_id=convo.id)

    return render(request, 'core/initiate_booking.html', {'artist': artist})

def public_chat_room(request, guest_uuid):
    # Fetch conversation and artist profile in one single DB hit
    conversation = get_object_or_404(Conversation, guest_uuid=guest_uuid)
    
    # Use the related_name from your Booking model if possible
    booking = Booking.objects.filter(conversation=conversation).first()

    # Gatekeeper check
    if not booking or booking.status != "Accepted":
        messages.error(request, "This secure channel is inactive. Waiting for artist approval.")
        return redirect('core:home') 

    # Security check
    session_key = f"guest_chat_{guest_uuid}"
    if not request.session.get(session_key) and not request.user == conversation.receiver:
        messages.error(request, "Your session has expired. Please use your original link.")
        return redirect('core:home')

    # Render with the messages
    return render(request, 'core/chat_box.html', {
        'conversation': conversation,
        'booking': booking,
        'chat_messages': conversation.messages.all(), # Meta ordering handles the rest
        'is_guest': True
    })


@login_required
def chat_room(request, room_id):
    # Security: Only the assigned Artist (receiver) can access this
    conversation = get_object_or_404(Conversation, id=room_id, receiver=request.user)
    
    # Using your specific model name: ChatMessage
    chat_messages = conversation.messages.all().order_by('timestamp')
    
    # Link to the booking for the sidebar info
   
    booking = Booking.objects.filter(conversation=conversation).first()

    return render(request, 'core/artist_messenger.html', {
        'conversation': conversation,
        'booking': booking,
        'chat_messages': chat_messages,
        'is_guest': False
    })


def send_chat_magic_link(request, convo):
    """Sends a recovery link using the current dynamic domain"""
    if not convo.visitor_email:
        return

    # Dynamically builds the absolute URL (works on localhost and production)
    chat_url = request.build_absolute_uri(
        reverse('core:brand_chat_room', kwargs={'guest_uuid': convo.guest_uuid})
    )
    
    brand_name = convo.receiver.brand.brand_name if hasattr(convo.receiver, 'brand') else "the Brand"
    
    subject = f"Secure Chat Link: {brand_name}"
    message = (
        f"Hi {convo.guest_name or 'there'},\n\n"
        f"Your inquiry with {brand_name} has been received.\n\n"
        f"If you ever close your browser or lose your way, use this private link to return to the chat:\n"
        f"{chat_url}\n\n"
        f"Regards,\nThe Azers Squad Team"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [convo.visitor_email],
        fail_silently=True,
    )

def start_brand_chat(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject_type')
        msg_text = request.POST.get('message')

        # 1. Create the high-end conversation
        convo = Conversation.objects.create(
            receiver=brand.user,
            is_guest_chat=not request.user.is_authenticated,
            guest_name=name if not request.user.is_authenticated else None,
            visitor_email=email,
            subject_type=subject
        )
        
        if request.user.is_authenticated:
            convo.participants.add(request.user)

        # 2. Send the first message as the 'System/Lead' summary
        ChatMessage.objects.create(
            conversation=convo,
            sender=request.user if request.user.is_authenticated else None,
            is_from_guest=not request.user.is_authenticated,
            text=f"INITIAL INQUIRY - {subject}:\n{msg_text}"
        )

        # 3. Create a Lead entry for Brand Analytics
        Lead.objects.create(brand=brand)

        # 4. Trigger the Magic Link via Email
        send_chat_magic_link(request, convo)

        # 5. Handle session for security
        if not request.user.is_authenticated:
            request.session[f"guest_chat_{convo.guest_uuid}"] = True

        messages.success(request, "Chat initialized! A recovery link has been sent to your email.")
        return redirect("core:brand_chat_room", guest_uuid=convo.guest_uuid)

    return render(request, "core/brand_inquiry_form.html", {"brand": brand})


def brand_chat_room(request, guest_uuid):
    conversation = get_object_or_404(Conversation, guest_uuid=guest_uuid)
    
    # Identify the user
    is_brand = request.user.is_authenticated and request.user == conversation.receiver
    has_session = bool(request.session.get(f"guest_chat_{guest_uuid}"))
    is_participant = request.user.is_authenticated and conversation.participants.filter(id=request.user.id).exists()

    context = {
        "conversation": conversation,
        "chat_messages": conversation.messages.all().order_by('timestamp'),
    }

    # 1. Route to Brand View
    if is_brand:
        context["is_receiver"] = True
        return render(request, "core/chat_brand_view.html", context)
    
    # 2. Route to Guest/Client View
    if has_session or is_participant:
        context["is_receiver"] = False
        return render(request, "core/chat_guest_view.html", context)

    # 3. Security Fallback
    messages.error(request, "Access denied. Please use the link sent to your email.")
    return redirect("core:home")

# def brand_chat_room(request, guest_uuid):
#     conversation = get_object_or_404(Conversation, guest_uuid=guest_uuid)
    
#     # Check if the receiver is actually a Brand
#     if not hasattr(conversation.receiver, "brand"):
#         messages.error(request, "Invalid chat room.")
#         return redirect("core:home")

#     # Security check: User must be either the Receiver, a Participant, or have a valid Guest Session
#     has_session = bool(request.session.get(f"guest_chat_{guest_uuid}"))
#     is_receiver = request.user.is_authenticated and request.user == conversation.receiver
#     is_participant = (
#         request.user.is_authenticated
#         and conversation.participants.filter(id=request.user.id).exists()
#     )

#     if not (has_session or is_receiver or is_participant):
#         # If no session, they must fill the form again or use the Magic Link from email
#         messages.error(request, "Your secure chat session has expired. Please use the link sent to your email.")
#         return redirect("core:home")

#     return render(
#         request,
#         "core/brands_chat.html",
#         {
#             "conversation": conversation,
#             "chat_messages": conversation.messages.all().order_by('timestamp'),
#             "is_receiver": is_receiver,
#         },
#     )

def send_msg(request, convo_id):
    if request.method == "POST":
        conversation = get_object_or_404(Conversation, id=convo_id)
        text = request.POST.get('text')
        image = request.FILES.get('image')

        if text or image:
            ChatMessage.objects.create(
                conversation=conversation,
                sender=request.user if request.user.is_authenticated else None,
                is_from_guest=not request.user.is_authenticated,
                text=text,
                image=image
            )

            if request.headers.get('HX-Request'):
                from django.http import HttpResponse
                return HttpResponse(status=204)
        
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))
        
    #     return redirect("core:brand_chat_room", guest_uuid=conversation.guest_uuid)
    
    # return redirect("core:home")

def brand_ticket_manager(request):
    # Get the brand associated with the logged-in user
    brand = request.user.brand 
    tickets = Ticket.objects.filter(brand=brand)
    
    # Get all pending payments for this brand's tickets
    pending_verifications = TicketPurchase.objects.filter(
        ticket__brand=brand, 
        status='pending'
    )

    context = {
        'tickets': tickets,
        'pending_verifications': pending_verifications,
    }
    return render(request, 'core/ticket_manager.html', context)

logger = logging.getLogger(__name__)

@login_required
@require_POST
def approve_ticket(request, purchase_id):
    purchase = get_object_or_404(TicketPurchase, id=purchase_id)
    
    if request.user.brand != purchase.ticket.brand:
        return HttpResponseForbidden("You do not have permission to approve this ticket.")

    purchase.status = 'approved'
    purchase.issued_pass_id = f"AZR-{purchase.ticket.id}-{purchase.id}"
    purchase.save()

    # Try to notify buyer, but never block approval if mail server is unreachable.
    subject = f"Your Access Pass: {purchase.ticket.event_name}"
    message = (
        f"Hello {purchase.user_name},\n\nYour payment has been verified! \n\n"
        f"Event: {purchase.ticket.event_name}\n"
        f"Pass ID: {purchase.issued_pass_id}\n"
        f"Show this ID at the entrance.\n\nEnjoy the event!"
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [purchase.email],
            fail_silently=False,
        )
        messages.success(request, "Ticket approved and pass email sent.")
    except Exception:
        logger.exception("Ticket approved but pass email failed for purchase_id=%s", purchase.id)
        messages.warning(
            request,
            "Ticket approved, but email could not be sent right now. Please retry mail later.",
        )

    return redirect('core:ticket_manager')
    
    


@login_required
def add_ticket(request):
    brand = request.user.brand
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.brand = brand
            ticket.save()
            return redirect('core:ticket_manager')
    else:
        form = TicketForm()
    
    return render(request, 'core/add_ticket.html', {'form': form})


def purchase_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        email = request.POST.get('email') # Capture the guest email
        user_photo = request.FILES.get('user_photo')
        payment_receipt = request.FILES.get('payment_receipt')

        # Create the purchase record
        TicketPurchase.objects.create(
            ticket=ticket,
            user_name=user_name,
            email=email,
            user_photo=user_photo,
            payment_receipt=payment_receipt,
            status='pending'
        )
        return render(request, 'core/purchase_success.html', {'ticket': ticket, 'email': email})

    return render(request, 'core/purchase_ticket.html', {'ticket': ticket})

def view_digital_pass(request, pass_id):
    # Look up the ticket using that unique serial number we generated
    purchase = get_object_or_404(TicketPurchase, issued_pass_id=pass_id, status='approved')
    return render(request, 'core/digital_pass.html', {'purchase': purchase})
