from django.contrib import admin
from .models import BookableItem, BookingTimeSlot


@admin.register(BookableItem)
class BookableItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'capacity']
    search_fields = ['name', 'info']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'capacity', 'is_active')
        }),
        ('Details', {
            'fields': ('info',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingTimeSlot)
class BookingTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['bookable_item', 'time_start', 'time_length', 'status', 'time_end']
    list_filter = ['status', 'bookable_item', 'time_start']
    search_fields = ['bookable_item__name']
    list_editable = ['status']
    ordering = ['time_start']
    date_hierarchy = 'time_start'
    
    fieldsets = (
        (None, {
            'fields': ('bookable_item', 'status')
        }),
        ('Time Details', {
            'fields': ('time_start', 'time_length')
        }),
    )
    
    def time_end(self, obj):
        return obj.time_end
    time_end.short_description = 'End Time'