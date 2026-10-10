from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(label="First name", max_length=150, required=False,
                                 help_text="Optional. Used to greet you on your dashboard.")
    email = forms.EmailField(label="Email address", required=False,
                             help_text="Optional. Not shared with anyone.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")
        self.fields["username"].widget.attrs.update({"autocapitalize": "none", "autocomplete": "username"})
