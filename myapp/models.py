from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

# Certification Post Model
class CertificationPost(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Español'),
        ('fr', 'Français'),
        ('de', 'Deutsch'),
        ('kr', '한국어'),       # Korean
        ('jp', '日本語'),       # Japanese
        ('cn', '中文'),         # Chinese
        ('ru', 'Русский'),      # Russian
        ('pt', 'Português'),    # Portuguese
        ('it', 'Italiano'),     # Italian
        ('hi', 'हिन्दी'),       # Hindi
        ('ar', 'العربية'),      # Arabic
        ('bn', 'বাংলা'),       # Bengali
        ('ms', 'Bahasa Melayu'), # Malay
        ('id', 'Bahasa Indonesia'), # Indonesian
        ('vi', 'Tiếng Việt'),   # Vietnamese
        ('tr', 'Türkçe'),       # Turkish
        ('th', 'ไทย'),          # Thai
        ('nl', 'Nederlands'),   # Dutch
        ('pl', 'Polski'),       # Polish
        ('sv', 'Svenska'),      # Swedish
        ('no', 'Norsk'),        # Norwegian
        ('da', 'Dansk'),        # Danish
        ('fi', 'Suomi'),        # Finnish
        ('el', 'Ελληνικά'),     # Greek
        ('he', 'עברית'),        # Hebrew
        # Add more languages as needed
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='certifications/', blank=True, null=True)
    image_logo = models.ImageField(upload_to='certifications/', blank=True, null=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')  # New language field
    price = models.DecimalField(max_digits=10, decimal_places=2)
    num_tests = models.IntegerField(default=4)
    time_limit = models.IntegerField(default=90)


    course_description = models.TextField(null=True)
    review_mode_description = models.TextField(null=True)
    timed_mode_description = models.TextField(null=True)
    practice_exam_translate = models.CharField(max_length=200, null=True)
    why_this_course_stands_out = models.TextField(null=True)
    what_you_will_gain = models.TextField(null=True)
    course_highlights = models.TextField(null=True)
    who_should_take_this_course = models.TextField(null=True)
    course_requirements = models.TextField(null=True)
    join_today = models.TextField(null=True)
    difficulty = models.CharField(max_length=200, null=True)
    duration = models.CharField(max_length=200, null=True)
    exam_format = models.CharField(max_length=200, null=True)
    number_of_practices = models.CharField(max_length=100, null=True)
    default_count = models.IntegerField(default=4)
    passing_score = models.IntegerField(default=75)

    def get_active_discount(self):
        now = timezone.now()
        active_discounts = self.discounts.filter(start_date__lte=now, end_date__gte=now)
        if active_discounts.exists():
            return active_discounts.order_by('-percentage').first()
        return None

    def get_discounted_price(self):
        discount = self.get_active_discount()
        if discount:
            return self.price * (Decimal('1') - discount.percentage / Decimal('100'))
        return self.price

    def __str__(self):
        return self.title


class CertificationTest(models.Model):
    certification_post = models.ForeignKey(CertificationPost, on_delete=models.CASCADE, related_name='tests')
    test_number = models.PositiveIntegerField()
    json_file_path = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('certification_post', 'test_number')
        ordering = ['test_number']

    def __str__(self):
        return f"{self.certification_post.title} - Test {self.test_number}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(CertificationPost, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.post.title}"

    
class PurchasedCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(CertificationPost, on_delete=models.SET_NULL, null=True, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    stripe_transaction_id = models.CharField(max_length=255, blank=True, null=True)  # New field
    completed_exams = models.JSONField(default=dict, blank=True)
    has_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(CertificationPost, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField(default=5)  # Rating out of 5
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} - {self.course}"
    



class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    excerpt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    html_file_path = models.CharField(max_length=200, null=True)  # Path to the HTML file

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Discount(models.Model):
    name = models.CharField(max_length=255)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 20.00 for 20%
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    posts = models.ManyToManyField('CertificationPost', related_name='discounts', blank=True)

    def __str__(self):
        return self.name

    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
