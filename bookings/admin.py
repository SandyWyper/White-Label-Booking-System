from django.contrib import admin
from .models import BookableItem, BookingTimeSlot, Booking


@admin.register(BookableItem)
class BookableItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'info']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'capacity', 'is_active')
        }),
        ('Additional Information', {
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


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'bookable_item', 'start_time', 'created_at']
    list_filter = ['time_slot__bookable_item', 'created_at', 'time_slot__time_start']
    search_fields = ['user__username', 'user__email', 'time_slot__bookable_item__name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'time_slot')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def bookable_item(self, obj):
        return obj.time_slot.bookable_item.name
    bookable_item.short_description = 'Bookable Item'
    
    def start_time(self, obj):
        return obj.time_slot.time_start
    start_time.short_description = 'Start Time'