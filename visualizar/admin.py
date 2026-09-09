from django.contrib import admin
from .models import Feedback, UserProfile, UserMission

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'age',
        'is_working',
        'work_experience_time',
        'overall_rating', 
        'rating_design', 
        'rating_usability', 
        'rating_vocational_test', 
        'favorite_feature', 
        'created_at'
    )
    list_filter = (
        'is_working',
        'work_experience_time',
        'overall_rating', 
        'rating_design', 
        'rating_usability', 
        'rating_vocational_test', 
        'created_at'
    )
    search_fields = (
        'user__username', 
        'user__email', 
        'user__first_name', 
        'favorite_feature', 
        'suggestions'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'total_xp', 'gems', 'streak_days', 'last_activity_date')
    search_fields = ('user__username', 'user__email', 'user__first_name')
    list_filter = ('level', 'last_activity_date')

@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'mission_code', 'completed_at')
    search_fields = ('user__username', 'mission_code')
    list_filter = ('mission_code', 'completed_at')
