from django.urls import path
from . import views

urlpatterns = [
    path('api/auth/signup/', views.signup_user, name='signup_user'),
    path('api/auth/login/', views.login_user, name='login_user'),
    path('api/auth/me/', views.me_user, name='me_user'),
    path('api/auth/debug/', views.debug_auth, name='debug_auth'),
    path('api/auth/google/login/', views.google_login, name='google_login'),
    path('api/auth/google/callback/', views.google_callback, name='google_callback'),
    path('api/auth/logout/', views.logout_user, name='logout_user'),
    path('api/auth/profile/', views.update_profile, name='update_profile'),
    path('api/auth/change-password/', views.change_password, name='change_password'),
    path('api/auth/change-password/otp/request/', views.request_change_password_otp, name='request_change_password_otp'),
    path('api/auth/change-password/otp/verify/', views.verify_change_password_otp, name='verify_change_password_otp'),
    path('api/auth/delete-account/', views.delete_account, name='delete_account'),
    path('api/summarize/', views.summarize_document, name='summarize_document'),
    path('api/summarize/stream/', views.summarize_document_stream, name='summarize_document_stream'),
    path('api/uploads/preflight/', views.preflight_upload, name='preflight_upload'),
    path('api/uploads/<int:upload_id>/summarize/', views.summarize_upload, name='summarize_upload'),

    path('api/uploads/', views.list_uploads, name='list_uploads'),
    path('api/uploads/<int:upload_id>/', views.get_upload, name='get_upload'),
    path('api/uploads/<int:upload_id>/download/', views.download_upload, name='download_upload'),

    # Payments (Razorpay - test mode)
    path('api/payments/razorpay/config/', views.razorpay_config, name='razorpay_config'),
    path('api/payments/razorpay/create-order/', views.razorpay_create_order, name='razorpay_create_order'),
    path('api/payments/razorpay/verify/', views.razorpay_verify_payment, name='razorpay_verify_payment'),
]

