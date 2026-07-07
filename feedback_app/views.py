from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import FeedbackForm
from .models import Feedback


def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your feedback has been saved. Thank you.")
            return redirect("feedback_app:feedback")
    else:
        form = FeedbackForm()

    latest_feedback = Feedback.objects.order_by("-created_at")[:5]
    return render(
        request,
        "feedback_app/feedback.html",
        {"form": form, "latest_feedback": latest_feedback},
    )

# Create your views here.
