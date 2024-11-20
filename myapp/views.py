from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView, redirect_to_login
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User
from .models import CertificationPost, Cart, PurchasedCourse, Review, Post, CertificationTest
from django.db.models import Q
from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
import json
from .forms import RegisterForm, ReviewForm, EditProfileForm, DeleteAccountForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import get_user_model
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.templatetags.static import static
from django.utils.safestring import mark_safe
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
from django.core.paginator import Paginator

# Create your views here.
def index(request):
    query = request.GET.get('q', '')  # Get the search query from the URL
    language = request.GET.get('language')  # Get the selected language from the URL

    # Filter posts based on search query and selected language
    posts = CertificationPost.objects.all()
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if language and language != 'all':
        posts = posts.filter(language=language)  # Filter by language if selected
    # Paginate the posts
    paginator = Paginator(posts, 9)  # Show 9 posts per page
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    return render(request, 'home.html', {'posts': posts, 'query': query, 'language': language})

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse_lazy('index')
    
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(reverse('reset_password_confirm', args=[uid, token]))

            # Send email
            subject = 'Password Reset Request'
            message = render_to_string('reset_password_email.html', {
                'reset_url': reset_url,
                'user': user
            })
            send_mail(subject, message, 'certsmango@gmail.com', [user.email])

            messages.success(request, 'If the email exists in our system, a password reset link has been sent.')
            return redirect('login')
        except User.DoesNotExist:
            messages.success(request, 'If the email exists in our system, a password reset link has been sent.')
            return redirect('forgot_password')

    return render(request, 'forgot_password.html')

def reset_password_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset. You can now log in with your new password.')
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        return render(request, 'reset_password_confirm.html', {'form': form})
    else:
        messages.error(request, 'The reset link is invalid, possibly because it has already been used.')
        return redirect('forgot_password')
    

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Save the user as inactive initially
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Generate the verification token and unique ID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Create the verification URL
            verification_url = request.build_absolute_uri(
                reverse('email_verification', kwargs={'uidb64': uid, 'token': token})
            )

            # Render the email content
            subject = 'Verify your email address'
            message = render_to_string('verification_email.html', {
                'user': user,
                'verification_url': verification_url,
            })

            # Send the verification email
            send_mail(subject, message, 'certsmango@gmail.com', [user.email])

            messages.success(request, 'A verification email has been sent to your email address. Please verify your account.')
            return redirect('login')  # Redirect to login or other appropriate page
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def email_verification(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been successfully verified. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('register')



def exam_detail(request, id):
    post = get_object_or_404(CertificationPost, id=id)
    is_purchased = False

    # Check if the user is authenticated before accessing purchased courses
    if request.user.is_authenticated:
        is_purchased = PurchasedCourse.objects.filter(user=request.user, course=post).exists()
    enrollment_count = PurchasedCourse.objects.filter(course=post).count()
    reviews = Review.objects.filter(course=post).order_by('-created_at')[:5]
    # Query for other courses in the same language
    other_courses = CertificationPost.objects.filter(language=post.language).exclude(id=id)[:4]  # Limit to 4 courses

    return render(request, 'post.html', {
        'course': post,
        'is_purchased': is_purchased,
        'other_courses': other_courses,
        'enrollment_count': enrollment_count,
        'reviews': reviews,
    })



###   MY CART SYSTEM
def my_cart(request):
    if not request.user.is_authenticated:
        messages.info(request, "You need to be logged in to view your cart.")
        return redirect_to_login(request.get_full_path())  # Redirect to login page
    
    # Fetch all cart items for the logged-in user
    cart_items = Cart.objects.filter(user=request.user)
    return render(request, 'my_cart.html', {'cart_items': cart_items})


def add_to_cart(request, id):
    if not request.user.is_authenticated:
        messages.info(request, "You need to be logged in to add to your cart.")
        return redirect_to_login(request.get_full_path())  # Redirect to login page
    course = get_object_or_404(CertificationPost, id=id)
    # Use get_or_create to prevent duplicate entries
    Cart.objects.get_or_create(user=request.user, post=course)
    return redirect('my_cart')

@login_required
def remove_from_cart(request, id):
    cart_item = get_object_or_404(Cart, user=request.user, post_id=id)
    cart_item.delete()
    return redirect('my_cart')




###   MY LEARNING SYSTEM
def my_learning(request):
    if not request.user.is_authenticated:
        messages.info(request, "You need to be logged in to view your courses")
        return redirect_to_login(request.get_full_path())  # Redirect to login page
    purchased_courses = PurchasedCourse.objects.filter(user=request.user)

    course_progress = []

    for item in purchased_courses:
        course = item.course

        # Total exams for the course
        total_exams = course.num_tests * 2# Multiply by 2 for two modes

        # Exams completed by the user for this course
        completed_exams = item.completed_exams  # This is a dictionary

        # Count the number of modes completed
        completed_modes_count = sum(len(modes) for modes in completed_exams.values())

        # Calculate percentage
        if total_exams > 0:
            progress_percentage = int((completed_modes_count / total_exams) * 100)
        else:
            progress_percentage = 0

        course_progress.append({
            'course_item': item,
            'progress_percentage': progress_percentage
        })

    context = {
        'course_progress': course_progress,
    }

    return render(request, 'my_learning.html', context)


def write_review(request, course_id):
    course = get_object_or_404(CertificationPost, id=course_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.course = course
            review.save()
            return redirect('my_learning')
    else:
        form = ReviewForm()
    
    return render(request, 'write_review.html', {'form': form, 'course': course})


@csrf_exempt  # For simplicity; ensure CSRF protection is handled properly
@login_required
def update_exam_progress(request):
    if request.method == 'POST':
        user = request.user
        course_id = request.POST.get('course_id')
        exam_number = request.POST.get('exam_number')
        mode = request.POST.get('mode')

        # Get the PurchasedCourse object
        try:
            purchased_course = PurchasedCourse.objects.get(user=user, course_id=course_id)
        except PurchasedCourse.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Purchased course not found'}, status=400)

        # Get the current completed_exams data
        completed_exams = purchased_course.completed_exams

        print(completed_exams)

        # Update the completed_exams data
        exam_key = f"exam_{exam_number}"
        modes_completed = completed_exams.get(exam_key, [])
        if mode not in modes_completed:
            modes_completed.append(mode)
            completed_exams[exam_key] = modes_completed
            # Save the updated data
            purchased_course.completed_exams = completed_exams
            purchased_course.save()

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)



def purchase_course(request, course_id):
    if not request.user.is_authenticated:
        messages.info(request, "You need to be logged in to purchase courses")
        return redirect_to_login(request.get_full_path())  # Redirect to login page
    # Get the course
    # Get the course
    course = get_object_or_404(CertificationPost, id=course_id)
    
    # Check if the user already purchased this course
    if PurchasedCourse.objects.filter(user=request.user, course=course).exists():
        messages.info(request, "You have already purchased this course.")
        return redirect('my_learning')
    
    # Set Stripe API key
    stripe.api_key = settings.STRIPE_SECRET_KEY
    YOUR_DOMAIN = 'https://mangocerts.com'  # Replace with your actual domain

    # Create a Stripe Checkout session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.title,
                    },
                    'unit_amount': int(course.price * 100),  # Price in cents
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=YOUR_DOMAIN + reverse('success'),
        cancel_url=YOUR_DOMAIN + reverse('cancel'),
        client_reference_id=request.user.id,
        metadata={
            'course_id': course_id  # Pass course_id here for access in the webhook
        }
    )
    return redirect(checkout_session.url, code=303)


def success_view(request):
    # Display a success message to the user
    return render(request, 'purchase_success.html', {
        'message': 'Thank you for your purchase! Your payment was successful.'
    })

def cancel_view(request):
    # Display a cancellation message to the user
    return render(request, 'purchase_cancelled.html', {
        'message': 'Your payment was canceled. Please try again if you wish to complete the purchase.'
    })

# views.py (updated stripe_webhook view)
@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        course_id = session.get('metadata', {}).get('course_id')
        # Get the user and course, and create PurchasedCourse
        if user_id and course_id:
            course = CertificationPost.objects.filter(id=course_id).first()
            user = User.objects.filter(id=user_id).first()
            if course and user:
                PurchasedCourse.objects.create(
                    user=user,
                    course=course,
                    stripe_transaction_id=event['data']['object']['id']  # Store the Charge ID
                )

                # Optionally, clear the course from the user's cart
                Cart.objects.filter(user=user, post=course).delete()

    return JsonResponse({'status': 'success'})


@login_required
def exam_selection(request, course_id):
    """
    Displays available exams/tests for a specific purchased course.
    """
    # Verify that the user has purchased the course
    purchased = PurchasedCourse.objects.filter(user=request.user, course_id=course_id).exists()
    if not purchased:
        messages.error(request, "You do not have access to this course.")
        return redirect('my_learning')  # Redirect to My Learning page

    # Get the course/exam details
    exam = get_object_or_404(CertificationPost, id=course_id)

    # Define the range of test numbers (e.g., 1 to 4)
    test_numbers = range(1, 5)  # Adjust as per your requirements

    language_code = exam.language
    translations = load_translations(language_code, exam)

    context = {
        'exam': exam,
        'test_numbers': test_numbers,
        'course_id': course_id,  # Pass course_id to the template if needed
        "translations":translations,
    }

    return render(request, 'exam_selection.html', context)

def load_translations(language_code, exam):
    """Load all translations from the static directory and select the appropriate language."""
    # Get the path to the translations.json static file
    
    translations_path = finders.find('translations.json')
    with open(translations_path, 'r', encoding='utf-8') as f:
        all_translations = json.load(f)

    language = all_translations.get(language_code, all_translations.get("en"))
    language['intro_text'] = language['intro_text'].replace("{{ exam.title }}", exam.title)
    language['intro_text_timed'] = language['intro_text_timed'].replace("{{ exam.title }}", exam.title)
    
    # Return the selected language dictionary, defaulting to English if not found
    return language



@login_required
def start_exam(request, course_id, test_number, mode='review'):
    # Verify that the user has purchased the course
    purchased = PurchasedCourse.objects.filter(user=request.user, course_id=course_id).exists()
    if not purchased:
        messages.error(request, "You do not have access to this course.")
        return redirect('my_learning')

    # Get the course/exam details
    exam = get_object_or_404(CertificationPost, id=course_id)

    # Get the specific test
    test = get_object_or_404(CertificationTest, certification_post=exam, test_number=test_number)

    # Retrieve JSON file path from the test model
    json_file_path = f'static/{test.json_file_path}'

    if not json_file_path:
        messages.error(request, "Exam data is not available.")
        return redirect('exam_selection', course_id=course_id)
    
    # Initialize the S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_READ_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_READ_SECRET_ACCESS_KEY,
        region_name="us-east-2"
    )

    # Attempt to read the JSON file from S3
    try:
        s3_response = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=json_file_path)
        questions_data = json.loads(s3_response['Body'].read().decode('utf-8'))
    except ClientError as e:
        messages.error(request, f"Could not load exam questions file from S3: {e}")
        return redirect('exam_selection', course_id=course_id)

    # Serialize questions data and other context variables
    questions_json = json.dumps(questions_data)
    test_numbers = exam.tests.values_list('test_number', flat=True).order_by('test_number')
    language_code = exam.language
    translations = load_translations(language_code, exam)

    context = {
        'exam': exam,
        'questions_json': questions_json,
        'test_number': test_number,
        'test_numbers': test_numbers,
        'current_exam_id': course_id,
        'mode': mode,
        'time_limit': exam.time_limit,
        "translations": translations
    }

    # Choose the template based on mode
    template_name = 'practice_exam_timed.html' if mode == 'timed' else 'practice_exam.html'
    return render(request, template_name, context)



def select_practice_test(request, exam_id):
    exam = get_object_or_404(CertificationPost, id=exam_id)
    context = {'exam': exam}
    return render(request, 'select_practice_test.html', context)


def about(request):
    return render(request, 'about.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_use(request):
    return render(request, 'terms_of_use.html')

def refund_policy(request):
    return render(request, 'refund_policy.html')

def contact_us(request):
    return render(request, 'contact_us.html')


def blog_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'blog_list.html', {'posts': posts})

def blog_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    html_file_path = static(post.html_file_path)  # Get the static file path

    # Read the HTML file content
    try:
        with open(f"static/{post.html_file_path}", "r") as file:
            html_content = file.read()
    except FileNotFoundError:
        html_content = "<p>Content not available</p>"

    context = {
        "post": post,
        "html_content": mark_safe(html_content),  # Mark HTML as safe to render
    }
    return render(request, "blog_detail.html", context)

def my_account(request):
    if not request.user.is_authenticated:
        messages.info(request, "You need to be logged in to view your account")
        return redirect_to_login(request.get_full_path())  # Redirect to login page
    user = request.user

    if request.method == 'POST':
        if 'edit_profile' in request.POST:
            edit_form = EditProfileForm(request.POST, instance=user)
            delete_form = DeleteAccountForm()
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('my_account')
        elif 'delete_account' in request.POST:
            edit_form = EditProfileForm(instance=user)
            delete_form = DeleteAccountForm(request.POST)
            if delete_form.is_valid():
                # Deactivate the user's account instead of deleting it
                user.is_active = False
                user.save()
                logout(request)
                messages.success(request, 'Your account has been deactivated successfully.')
                return redirect('index')  # Replace 'index' with your homepage URL name
    else:
        edit_form = EditProfileForm(instance=user)
        delete_form = DeleteAccountForm()

    # Fetch purchase history
    purchase_history = PurchasedCourse.objects.filter(user=user).order_by('-purchased_at')

    context = {
        'edit_form': edit_form,
        'delete_form': delete_form,
        'purchase_history': purchase_history,
    }

    return render(request, 'my_account.html', context)


def send_email_contact(request):
    if request.method == "POST":
        subject = request.POST.get("subject")
        topic = request.POST.get("topic")
        message_content = request.POST.get("message")
        course_id = request.POST.get("course") if topic == "Refund" else None

        # Ensure user is logged in for refund requests
        if topic == "Refund" and not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to request a refund.")
            return redirect("login")

        # Prepare full subject for email
        full_subject = f"{topic}: {subject}"

        # Include course info and user details in message if it's a refund request
        if topic == "Refund":
            user = request.user
            user_info = f"User ID: {user.id}\nName: {user.first_name} {user.last_name}\nEmail: {user.email}\n\n"
            message_content = user_info + message_content  # Add user info at the top of the message
            
            # Include purchased course details
            if course_id:
                try:
                    pur_course = PurchasedCourse.objects.get(id=course_id, user=user)
                    message_content = f"Course: {pur_course.course.title}\n\n" + message_content
                except PurchasedCourse.DoesNotExist:
                    messages.error(request, "The selected course does not exist.")
                    return redirect("contact_us")

        # Send email
        send_mail(
            subject=full_subject,
            message=message_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["certsmango@gmail.com"],  # Replace with your email
        )
        
        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact_us")
    
    # Fetch purchased courses for refund options
    purchased_courses = PurchasedCourse.objects.filter(user=request.user) if request.user.is_authenticated else []

    return render(request, "contact_us.html", {
        "purchased_courses": purchased_courses
    })