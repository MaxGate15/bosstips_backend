from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Games)
admin.site.register(BookingCode)
admin.site.register(Purchase)


@admin.register(Slips)
class SlipsAdmin(admin.ModelAdmin):
    filter_horizontal = ('games',)

    def has_add_permission(self, request):
        if BookingCode.objects.count() == 0:
            messages.set_level(request, messages.ERROR)
            messages.error(request, "Please add at least one Booking Code before adding a Slip.")
            return False
        return super().has_add_permission(request)
    # OR use filter_vertical


from django.contrib import admin
from .models import Notifications

class NotificationsAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

admin.site.register(Notifications, NotificationsAdmin)

from django.contrib import admin
from django.contrib import messages
from .models import Slips, BookingCode

# @admin.register(Slips)
# class SlipsAdmin(admin.ModelAdmin):


