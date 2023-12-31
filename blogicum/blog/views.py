from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm, ProfileForm
from .mixins import CommentDispatchMixin, ListViewMixin, PostDispatchMixin
from .models import Category, Comment, Post, User

PAGE_NUM = 10


class IndexListView(ListViewMixin, ListView):
    """CBV для ленты записей."""

    template_name = 'blog/index.html'
    ordering = ('-pub_date',)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(
            pub_date__lte=timezone.now(),
            category__is_published=True
        )


class CommentUpdateView(LoginRequiredMixin, CommentDispatchMixin, UpdateView):
    '''CBV для редактирования комментариев'''

    form_class = CommentForm


class CommentDeleteView(LoginRequiredMixin, CommentDispatchMixin, DeleteView):
    '''CBV удаления комментария'''

    pass


class ProfileListView(ListViewMixin, ListView):
    '''CBV профиля пользователя'''

    template_name = 'blog/profile.html'
    ordering = ('-pub_date',)

    def get_queryset(self) -> QuerySet[Any]:
        self.username = get_object_or_404(
            User, username=self.kwargs['username']
        )
        if self.username == self.request.user:
            # Без добавления order_by('-pub_date') тесты не проходят
            # Если убрать ordering в атрибутах тесты проваливаются
            return Post.objects.select_related(
                'author',
                'location',
                'category'
            ).filter(
                author=self.username
            ).annotate(comment_count=Count('comments')).order_by('-pub_date')
        return super().get_queryset().filter(
            pub_date__lte=timezone.now()
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['profile'] = self.username
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    '''CBV редактирования профиля'''

    model = User
    template_name = 'blog/user.html'
    form_class = ProfileForm
    success_url = 'blog:profile'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class CategoryListView(LoginRequiredMixin, ListViewMixin, ListView):
    '''CBV опубликованных категорий'''

    template_name = 'blog/category.html'
    ordering = ('-pub_date')
    category = None

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return super().get_queryset().filter(
            pub_date__lte=timezone.now(),
            category__is_published=True,
            category=self.category
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    '''CBV создания поста'''

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.pub_date > timezone.now():
            form.instance.published = False
            form.instance.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostDetailView(DetailView):
    '''CBV отдельного поста с комментариями к нему'''

    model = Post
    form_class = CommentForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        post = super().get_object()
        author = post.author
        if not self.request.user.is_authenticated or (
            author != self.request.user
        ):
            post = get_object_or_404(
                Post,
                is_published=True,
                pk=self.kwargs['post_id'],
                pub_date__lte=timezone.now(),
                category__is_published=True,
            )
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(post=self.object)
        return context


class PostUpdateView(LoginRequiredMixin, PostDispatchMixin, UpdateView):
    '''CBV редактирования поста'''

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostDeleteView(LoginRequiredMixin, PostDispatchMixin, DeleteView):
    '''CBV удаления поста'''

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(
            instance=Post.objects.get(pk=self.kwargs['post_id'])
        )
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    '''CBV создания комментария'''

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={"post_id": self.kwargs["post_id"]}
        )
