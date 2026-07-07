from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import UserQueryForm
from .models import UserQuery


def query_view(request):
    if request.method == "POST":
        form = UserQueryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your query has been submitted successfully.")
            return redirect("query_app:query")
    else:
        form = UserQueryForm()

    recent_queries = UserQuery.objects.order_by("-created_at")[:5]
    return render(
        request,
        "query_app/query.html",
        {"form": form, "recent_queries": recent_queries},
    )

# Create your views here.
