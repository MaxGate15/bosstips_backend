from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Games)
admin.site.register(BookingCode)


@admin.register(Slips)
class SlipsAdmin(admin.ModelAdmin):
    filter_horizontal = ('games',)  # OR use filter_vertical
