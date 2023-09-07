from typing import Any, Dict
from django import http
from django.db.models.query import QuerySet
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Category, Post, User, Comment
from .forms import ProfileForm, CommentForm


PAGE_NUM = 10


class IndexListView(ListView):
    """CBV для ленты записей."""
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGE_NUM
    ordering = ('-pub_date',)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).annotate(comment_count=Count('comments'))


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    '''CBV для редактирования комментариев'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            get_object_or_404(
                Comment,
                pk=kwargs['comment_id'],
                author=request.user
            )
            return super().dispatch(request, *args, **kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    '''CBV удаления комментария'''
    model = Comment
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):
        comment = super().get_object(queryset=queryset)
        if not self.request.user.is_authenticated:
            raise PermissionDenied(
                "Вы не аутентифицированы и не можете удалить этот комментарий."
            )
        if (
            self.request.user != comment.author
            and not self.request.user.is_superuser
        ):
            raise PermissionDenied(
                'Вы не можете удалить этот комментарий,'
                'так как не являетесь его автором или администратором.'
            )
        return comment

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class ProfileListView(ListView):
    '''CBV профиля пользователя'''
    model = Post
    form_class = ProfileForm
    template_name = 'blog/profile.html'
    paginate_by = PAGE_NUM
    slug_url_kwarg = 'username'
    ordering = ('-pub_date',)

    def get_queryset(self) -> QuerySet[Any]:
        self.username = get_object_or_404(
            User, username=self.kwargs['username']
        )
        return super().get_queryset().filter(
            author=self.username
        ).annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['profile'] = self.username
        return context


class ProfileDetailView(LoginRequiredMixin, DetailView):
    '''CBV страницы пользователя'''
    model = User
    template_name = 'blog/profile.html'
    paginate_by = PAGE_NUM

    def get_queryset(self) -> QuerySet[Any]:
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        if self.author == self.request.user:
            queryset = Post.objects.filter(
                author=self.author
            ).order_by('-pub_date').annotate(
                comment_count=Comment.objects.count
            )
        else:
            queryset = super().get_queryset().filter(author=self.author)
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    '''CBV редактирования профиля'''
    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'username', 'email']
    success_url = 'blog:profile'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class CategoryListView(LoginRequiredMixin, ListView):
    '''CBV опубликованных категорий'''
    model = Post
    template_name = 'blog/category.html'
    paginate_by = PAGE_NUM
    slug_url_kwarg = 'category_slug'
    ordering = ('-pub_date')
    category = None

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
            category__slug=self.kwargs['category_slug'],
            category=self.category
        ).annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['post_list'] = self.kwargs['category_slug']
        context['category'] = self.kwargs['category_slug']
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    '''CBV создания поста'''
    model = Post
    fields = ('title', 'text', 'pub_date', 'location', 'category', 'image')
    template_name = 'blog/create.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        if post.pub_date > timezone.now():
            post.published = False
            post.save()
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
    context_object_name = 'post'

    def dispatch(self, request, *args, **kwargs):
        """При попытке пользователя, не являющегося автором поста,
        зайти на неопубликованный пост, его перекинет на главную."""
        if self.get_object().author != self.request.user and (
                self.get_object().is_published is False or
                self.get_object().category.is_published is False or
                self.get_object().pub_date > timezone.now()
        ):
            raise http.Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    '''CBV редактирования поста'''
    model = Post
    fields = (
        'title',
        'text',
        'pub_date',
        'location',
        'category',
        'image',
        'is_published'
    )
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(
                Post,
                pk=kwargs['post_id'],
            )
        if not request.user.is_authenticated:
            return redirect(reverse(
                'blog:post_detail',
                kwargs={'post_id': self.kwargs['post_id']})
            )
        if request.user != post.author:
            return redirect(reverse(
                'blog:post_detail',
                kwargs={'post_id': self.kwargs['post_id']})
            )
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    '''CBV удаления поста'''
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            post = get_object_or_404(
                Post,
                pk=kwargs['post_id'],
            )
            if request.user == post.author:
                return super().dispatch(request, *args, **kwargs)
            else:
                return redirect(reverse(
                    'blog:post_detail',
                    kwargs={'post_id': kwargs['post_id']}))
        else:
            return redirect(reverse(
                'blog:post_detail',
                kwargs={'post_id': kwargs['post_id']})
            )

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
