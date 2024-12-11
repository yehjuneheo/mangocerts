from django.contrib import admin
from .models import CertificationPost, Cart, PurchasedCourse, Review, Post, CertificationTest, Discount


# Register your models here
admin.site.register(CertificationPost)
admin.site.register(Cart)
admin.site.register(PurchasedCourse)
admin.site.register(Review)
admin.site.register(Post)
admin.site.register(CertificationTest)

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'start_date', 'end_date')
    filter_horizontal = ('posts',)

admin.site.register(Discount, DiscountAdmin)

