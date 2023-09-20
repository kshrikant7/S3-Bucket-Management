from django import forms

class FileDeletionForm(forms.Form):
    bucket_name = forms.ChoiceField(choices=(), required=True)
    file_keys = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=False)