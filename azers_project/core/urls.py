from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),

    # Authentication
    path("signup/", views.member_signup, name="member_signup"), 
    path("signup/artist/", views.artist_signup, name="artist_signup"),
    path("signup/brand/", views.brand_signup, name="brand_signup"),
    # path("signup/seller/", views.seller_signup, name="seller_signup"),
    path("login/", views.custom_login, name="login"),

    # path("login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="core:home"), name="logout"),

    # Artist
    path("artists/", views.artist_list, name="artist_list"),
    path('brands/', views.brand_list, name='brand_list'),
    path("artist/<int:pk>/", views.artist_detail, name="artist_detail"),
    # path("seller/<int:seller_id>/", views.seller_detail, name="seller_detail"),

    path("artist/dashboard/", views.artist_dashboard, name="artist_dashboard"),
    path("artist/edit/", views.edit_artist_profile, name="edit_artist_profile"),
    path("artist/<int:artist_id>/book/", views.book_artist, name="book_artist"),
    # 2. The Guest Tracking Page (The link in the email)
    # Using uuid:secret_id makes it impossible to guess other people's bookings
    path('booking/status/<uuid:secret_id>/', views.guest_booking_detail, name='guest_booking_detail'),

    # 3. The Artist Action (Internal Dashboard Logic)
    path('booking/update/<int:booking_id>/', views.artist_update_booking, name='artist_update_booking'),
    path('booking/receipt/<uuid:secret_id>/pdf/', views.download_booking_pdf, name='pdf_receipt'),

    # Booking
    # path("bookings/", views.booking_list, name="booking_list"),
    # path("logout/", LogoutView.as_view(next_page="core:home"), name="logout"),

    # Portfolio URLs
    path("artist/portfolio/", views.portfolio_list, name="portfolio_list"),
    path("artist/portfolio/add/", views.add_portfolio_item, name="add_portfolio_item"),
    path("artist/portfolio/delete/<int:item_id>/", views.delete_portfolio_item, name="delete_portfolio_item"),
    path("awaiting-approval/", views.awaiting_approval, name="awaiting_approval"),

    path("brand/<int:pk>/", views.brand_detail, name="brand_detail"),
    path("brand/<int:brand_id>/chat/", views.start_brand_chat, name="start_brand_chat"),
    path("brand/chat/<uuid:guest_uuid>/", views.brand_chat_room, name="brand_chat_room"),
    path("brand/dashboard/", views.brand_dashboard, name="brand_dashboard"),
    path("brand/edit/", views.edit_brand_profile, name="edit_brand_profile"),

    # Product CRUD
    path("brand/product/add/", views.add_product, name="add_product"),
    path("brand/product/<int:pk>/edit/", views.edit_product, name="edit_product"),
    path("brand/product/<int:pk>/delete/", views.delete_product, name="delete_product"),
    path('brand/<int:brand_id>/inquiry/', views.send_inquiry, name='send_inquiry'),

    # Service CRUD
    path("brand/service/add/", views.add_service, name="add_service"),
    path("brand/service/<int:pk>/edit/", views.edit_service, name="edit_service"),
    path("brand/service/<int:pk>/delete/", views.delete_service, name="delete_service"),

    # Dashboard URLs
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    path('admin-dashboard/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    # Marketplace & Public Brand Store
    path("marketplace/", views.marketplace, name="marketplace"),
    # path("brand/store/<int:pk>/", views.brand_storefront, name="brand_storefront"),
    path('track-lead/<int:product_id>/', views.track_lead, name='track_lead'),

    path('brand/product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('brand/service/delete/<int:pk>/', views.delete_service, name='delete_service'),
    path('brand/product/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('brand/service/edit/<int:pk>/', views.edit_service, name='edit_service'),

    path('booking/verify/<uuid:secret_id>/', views.verify_payment, name='verify_payment'),

    path('book/<int:artist_id>/', views.initiate_booking_chat, name='initiate_booking'),
    path('chat/g/<uuid:guest_uuid>/', views.public_chat_room, name='public_chat_room'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('portal/<uuid:guest_uuid>/', views.public_chat_room, name='public_chat_room'),
    path('chat/send/<int:convo_id>/', views.send_msg, name='send_msg'),
    path('admin-panel/toggle/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),
    path('admin-panel/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('dashboard/tickets/', views.brand_ticket_manager, name='ticket_manager'),
    path('dashboard/tickets/approve/<int:purchase_id>/', views.approve_ticket, name='approve_ticket'),
    path('dashboard/tickets/add/', views.add_ticket, name='add_ticket'),
    path('ticket/purchase/<int:ticket_id>/', views.purchase_ticket, name='purchase_ticket'),
    path('pass/<str:pass_id>/', views.view_digital_pass, name='view_digital_pass'),
    # path('booking/pdf/<uuid:secret_id>/', views.download_booking_pdf, name='download_pdf'),
    


]
