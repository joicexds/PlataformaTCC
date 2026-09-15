from django.contrib import admin
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from .models import Feedback, UserProfile, UserMission
from django.contrib.auth.models import User

# Existing model admins

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
        'created_at',
    )
    list_filter = (
        'is_working',
        'work_experience_time',
        'overall_rating',
        'rating_design',
        'rating_usability',
        'rating_vocational_test',
        'created_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'favorite_feature',
        'suggestions',
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

# ---------- Custom admin dashboard ----------

class VisualizarAdminSite(admin.AdminSite):
    site_header = "Plataforma TCC – Admin Dashboard"
    site_title = "Admin"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='admin-dashboard'),
            path('user/<int:user_id>/feedbacks/', self.admin_view(self.user_feedbacks_view), name='admin-user-feedbacks'),
        ]
        return custom + urls

    def dashboard_view(self, request):
        total_feedback = Feedback.objects.count()
        avg_rating = Feedback.objects.aggregate(avg_overall=Avg('overall_rating'))['avg_overall'] or 0
        recent = (
            Feedback.objects
            .filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        chart_labels = [entry['day'].strftime('%Y-%m-%d') for entry in recent]
        chart_counts = [entry['count'] for entry in recent]
        users = User.objects.all().values('id', 'username', 'first_name', 'last_name', 'email')
        context = {
            'total_feedback': total_feedback,
            'avg_rating': round(avg_rating, 2),
            'chart_labels': chart_labels,
            'chart_counts': chart_counts,
            'users': users,
        }
        return render(request, 'admin/dashboard.html', context)

    def user_feedbacks_view(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        feedbacks = Feedback.objects.filter(user=user).order_by('-created_at')
        context = {'user': user, 'feedbacks': feedbacks}
        return render(request, 'admin/user_feedbacks.html', context)

# Instantiate custom admin site and register models
visualizar_admin_site = VisualizarAdminSite(name='visualizar_admin')
visualizar_admin_site.register(Feedback, FeedbackAdmin)
visualizar_admin_site.register(UserProfile, UserProfileAdmin)
visualizar_admin_site.register(UserMission, UserMissionAdmin)
visualizar_admin_site.register(User)
