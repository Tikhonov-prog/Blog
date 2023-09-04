from typing import Any, Dict
from django.db.models.query import QuerySet
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Post, User, Comment
from .forms import PostForm, ProfileForm, CommentForm


FIRST_FIVE_PUBLICATION = 5
PAGE_NUM = 10


def get_select_related():
    """Функция для наследования"""
    return Post.objects.select_related(
        'location',
        'category',
        'author'
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )


class IndexListView(ListView):
    """View функция Ленты записей."""
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGE_NUM
    ordering = ('-pub_date')

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).annotate(comment_count=Count('comments'))


class CommentUpdateView(UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        # Получаем объект по первичному ключу и автору или вызываем 404 ошибку.
        get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
            author=request.user
        )
        # Если объект был найден, то вызываем родительский метод,
        # чтобы работа CBV продолжилась.
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class CommentDeleteView(DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'comment_id'


class ProfileListView(ListView):
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


class ProfileDetailView(DetailView):
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


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = PAGE_NUM
    slug_url_kwarg = 'category_slug'
    ordering = ('-pub_date')

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
            category__slug=self.kwargs['category_slug']
        ).annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['post_list'] = self.kwargs['category_slug']
        context['category'] = self.kwargs['category_slug']
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
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
    model = Post
    form_class = CommentForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        # Получаем объект по первичному ключу и автору или вызываем 404 ошибку.
        get_object_or_404(Post, pk=kwargs['post_id'], author=request.user)
        # Если объект был найден, то вызываем родительский метод,
        # чтобы работа CBV продолжилась.
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        # Получаем объект по первичному ключу и автору или вызываем 404 ошибку.
        get_object_or_404(Post, pk=kwargs['post_id'], author=request.user)
        # Если объект был найден, то вызываем родительский метод,
        # чтобы работа CBV продолжилась.
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(self.request.user.get_username(),)
        )


class CommentCreateView(CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.post_data = get_object_or_404(
            Post,
            pk=self.kwargs['post_id'],
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
        return super().dispatch(request, *args, **kwargs)

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
