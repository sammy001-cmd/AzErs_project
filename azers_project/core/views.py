from decimal import Decimal, InvalidOperation
import email
# from os import name
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Portfolio
from .forms import PortfolioForm
from .models import Artist, Booking
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .models import Portfolio, Brand, Product, Service, BrandInquiry,Lead
from .forms import PortfolioForm, BrandProfileForm, ProductForm, ServiceForm
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
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
    print("DEBUG Featured brands:", featured_brands)  # <-- check console
    return render(request, "core/home.html", {
        "featured_artists": featured_artists,
        "featured_brands": featured_brands,
    })

# def home(request):
#     featured_artists = Artist.objects.filter(user__is_approved=True).order_by('-created_at')[:6]
#     featured_brands = Brand.objects.filter(user__is_approved=True).order_by('-created_at')[:6]
#     return render(request, "core/home.html", {
#         "featured_artists": featured_artists,
#         "featured_brands": featured_brands,
#     })




def artist_list(request):
    artists = Artist.objects.filter(user__is_approved=True)
    return render(request, "core/artist_list.html", {"artists": artists})


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
    
    # This prevents the 404: 
    # It tries to find the artist; if not found, it creates one on the fly.
    artist, created = Artist.objects.get_or_create(
        user=request.user, 
        defaults={'stage_name': request.user.username}
    )
    total_revenue = artist.bookings.filter(
        payment_status__in=["Paid", "Partially Paid"]
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0.00
    
    return render(request, "core/artist_dashboard.html", {"artist": artist, 'total_revenue':total_revenue})


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
    
    return render(request, "core/brand_dashboard.html", {
        "brand": brand,
        "products": products,
        "services": services,
    })


def brand_detail(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    return render(request, "core/brand_detail.html", {"brand": brand})

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
        return redirect('core:brand_public_profile', brand_id=brand.id)

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


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('core:home') # Keep non-admins out
        
    context = {
        'total_artists': User.objects.filter(role='artist').count(),
        'total_brands': User.objects.filter(role='brand').count(),
        'pending_users': User.objects.filter(is_approved=False).count(),
        'recent_users': User.objects.all().order_by('-date_joined')[:15],
    }
    return render(request, "core/admin_dashboard.html", context)


@login_required
# """using this view to approve users from the admin dashboard list (Ajas)"""
def approve_user(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Access Denied")
    
    user_to_approve = get_object_or_404(User, id=user_id)
    user_to_approve.is_approved = True
    user_to_approve.save()
    
    messages.success(request, f"User {user_to_approve.username} has been approved.")
    return redirect('core:admin_dashboard')


    # --- Marketplace Views ---

def marketplace(request):
    """Shows all products from all approved brands (General Marketplace)"""
    products = Product.objects.filter(brand__user__is_approved=True)
    return render(request, "core/marketplace.html", {"products": products})

def brand_storefront(request, pk):
    """Shows a specific brand's profile and all their products/services"""
    brand = get_object_or_404(Brand, pk=pk)
    products = brand.products.all()
    services = brand.services.all()
    return render(request, "core/brand_storefront.html", {
        "brand": brand,
        "products": products,
        "services": services,
    })



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

from django.shortcuts import render

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
        
        # Proper Try/Except for Decimal conversion
        try:
            deposit_input = request.POST.get('amount', '0')
            deposit = Decimal(deposit_input) if deposit_input else Decimal('0')
        except (InvalidOperation, ValueError):
            messages.error(request, "Please enter a valid numerical amount.")
            return redirect(request.path)

        # Premium Validation: 50% Rule
        min_deposit = artist.price_tag / 2
        if deposit < min_deposit:
            messages.error(request, f"Minimum 50% deposit (₦{min_deposit}) required.")
            return redirect(request.path)

        # Create the Booking
        booking = Booking.objects.create(
            artist=artist,
            customer_name=name,
            customer_email=email,
            event_date=date,
            amount_paid=0.00,
            total_quote=artist.price_tag,
            notes=request.POST.get('notes', '')
        )
        booking.update_payment_logic()
        
        # Build the Secret Guest URL
        full_url = request.build_absolute_uri(booking.get_absolute_url())

        # TRIGGER EMAIL: "Request Received"
        send_mail(
            subject=f"Request Sent: {artist.stage_name} @ Azers Squad",
            message=f"Hi {name},\n\nYour booking request for {artist.stage_name} has been sent! \n\nTrack status and pay balance here: {full_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        messages.success(request, "Request Sent! Check your email for your private tracking link.")
        return redirect('core:guest_booking_detail', secret_id=booking.secret_id)
    
    return render(request, "core/booking_form.html", {"artist": artist})

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
        full_url = request.build_absolute_uri(booking.get_absolute_url())

        if action == "accept":
            booking.status = "Accepted"
            
            # 1. Setup Email Context
            subject = f"APPROVED: {booking.artist.stage_name} is confirmed!"
            html_content = render_to_string('emails/booking_accepted.html', {
                'booking': booking,
                'full_url': full_url
            })
            text_content = strip_tags(html_content) # Fallback for old email apps

            # 2. Create Email Object
            msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [booking.customer_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, "Gig Accepted! The client has been emailed.")
            
        elif action == "decline":
            booking.status = "Declined"
            messages.warning(request, "Booking declined.")
            
        elif action == "complete":
            booking.status = "Completed"
            messages.success(request, "Gig marked as finished!")
            
        booking.save()
    
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