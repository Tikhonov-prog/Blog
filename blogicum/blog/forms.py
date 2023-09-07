from django import forms

from .models import Post, User, Comment


class PostForm(forms.ModelForm):
    '''Форма на основе модели Post'''
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'post': forms.DateInput(attrs={'type': 'date'})
        }


class ProfileForm(forms.ModelForm):
    '''Форма на основе встроенной модели User'''

    class Meta:
        model = User
        fields = '__all__'


class CommentForm(forms.ModelForm):
    ''''Форма на основе модели Comment'''

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            "text": forms.Textarea({"rows": "3"})
        }
