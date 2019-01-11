from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib import messages


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Your account has been created successfully! Now Login to your account!')
            return redirect("login")
    else:
        form = UserRegistrationForm()

    context = {
        "form": form,
        "title": "Registration"
    }
    return render(request, "users/register.html", context)
