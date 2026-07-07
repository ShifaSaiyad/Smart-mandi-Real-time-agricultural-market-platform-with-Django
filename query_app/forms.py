from django import forms

from .models import UserQuery


class UserQueryForm(forms.ModelForm):
    class Meta:
        model = UserQuery
        fields = ("name", "email", "phone_number", "subject", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"
