from django.contrib import admin
from .models import CertificationPost, Cart, PurchasedCourse, Review, Post, CertificationTest


# Register your models here
admin.site.register(CertificationPost)
admin.site.register(Cart)
admin.site.register(PurchasedCourse)
admin.site.register(Review)
admin.site.register(Post)
admin.site.register(CertificationTest)