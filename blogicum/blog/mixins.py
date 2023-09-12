from typing import Any

from django.db.models import Count
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .forms import PostForm
from .models import Comment, Post

PAGE_NUM = 10


class CommentDispatchMixin:
    '''Миксин проверяющий авторство комментатора'''
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
        )
        if request.user == comment.author:
            return super().dispatch(request, *args, **kwargs)
        return redirect(reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        ))


class PostDispatchMixin:
    '''Миксин проверяющий авторство постов'''

    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(
            Post,
            pk=kwargs['post_id'],
        )
        if request.user == post.author:
            return super().dispatch(request, *args, **kwargs)
        return redirect(reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        ))


class ListViewMixin:
    model = Post
    paginate_by = PAGE_NUM

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related(
            'author',
            'location',
            'category'
        ).filter(
            is_published=True
        ).annotate(comment_count=Count('comments'))
