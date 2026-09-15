from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg
from .models import Feedback

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard showing feedback summary and placeholder for graphs."""
    avg_ratings = Feedback.objects.aggregate(
        avg_design=Avg('rating_design'),
        avg_colors=Avg('rating_colors'),
        avg_typography=Avg('rating_typography'),
        avg_usability=Avg('rating_usability'),
        avg_vocational=Avg('rating_vocational_test'),
        avg_responsiveness=Avg('rating_responsiveness'),
        avg_overall=Avg('overall_rating'),
    )
    feedbacks = Feedback.objects.select_related('user').all()
    context = {
        'feedbacks': feedbacks,
        'avg_ratings': avg_ratings,
    }
    return render(request, 'admin_dashboard.html', context)
