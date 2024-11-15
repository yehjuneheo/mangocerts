from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('exams/<int:id>/', views.exam_detail, name='exam_detail'),
    path('register/', views.register, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),
    path('verify-email/<uidb64>/<token>/', views.email_verification, name='email_verification'),
    path('my_account/', views.my_account, name='my_account'),

    path('cart/', views.my_cart, name='my_cart'),  # Exams listing page
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:id>/', views.remove_from_cart, name='remove_from_cart'),

    path('my-learning/', views.my_learning, name='my_learning'),
    path('my-learning/<int:course_id>/write_review/', views.write_review, name='write_review'),
    path('update_exam_progress/', views.update_exam_progress, name='update_exam_progress'),
    path('purchase/<int:course_id>/', views.purchase_course, name='purchase_course'),
    path('success/', views.success_view, name='success'),
    path('cancel/', views.cancel_view, name='cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),


    path('my_exams/<int:course_id>/', views.exam_selection, name='exam_selection'),
    path('start_exam/<int:course_id>/<int:test_number>/', views.start_exam, name='start_exam'),
    path('start_exam/<int:course_id>/<int:test_number>/<str:mode>/', views.start_exam, name='start_exam'),
    
    path('about/', views.about, name='about'),  # About page
    path('blogs', views.blog_list, name='blog_home'),
    path('post/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('terms_of_use/', views.terms_of_use, name='terms_of_use'),
    path('refund_policy/', views.refund_policy, name='refund_policy'),
    path('contact_us/', views.send_email_contact, name='contact_us'),
]
