from django import forms

from .models import Post, User, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'post': forms.DateInput(attrs={'type': 'date'})
        }


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = '__all__'


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
