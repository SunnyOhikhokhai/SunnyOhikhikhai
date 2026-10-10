from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import SignUpForm


class FinplanLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "input")
        form.fields["username"].widget.attrs.update({"autocapitalize": "none"})
        return form


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to FINPLAN. Your account is ready.")
            return redirect("dashboard:home")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})
