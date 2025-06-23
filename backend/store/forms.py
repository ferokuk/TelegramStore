from django import forms
from .models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Category.objects.filter(parent__isnull=True)

        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        self.fields['parent'].queryset = queryset
