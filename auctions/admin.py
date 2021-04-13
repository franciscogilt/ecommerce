from django.contrib import admin
from .models import Category, Listing, Comment, Bid, User

# Register your models here.
admin.site.register(User)
admin.site.register(Listing)
admin.site.register(Comment)
admin.site.register(Bid)
admin.site.register(Category)