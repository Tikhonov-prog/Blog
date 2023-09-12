from django import forms

from .models import Comment, Post, User


class PostForm(forms.ModelForm):
    '''Форма на основе модели Post'''

    class Meta:
        model = Post
        exclude = ['author']
        widgets = {
            'post': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M:%S',
                attrs={'type': 'datetime-local'}
            )
        }


class ProfileForm(forms.ModelForm):
    '''Форма на основе встроенной модели User'''

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']


class CommentForm(forms.ModelForm):
    '''Форма на основе модели Comment'''

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            "text": forms.Textarea({"rows": "3"})
        }
