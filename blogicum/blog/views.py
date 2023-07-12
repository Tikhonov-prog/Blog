from django.contrib.auth.decorators import login_required
from typing import Any, Dict
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Post, Category, User, Comment
from .forms import PostForm, ProfileForm, CommentForm

FIRST_FIVE_PUBLICATION = 5


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
    paginate_by = 10

    def get_queryset(self):
        return get_select_related().annotate(comment_count=Comment('comments'))


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm
        context['comments'] = self.object.comments.all()
        return context


class ProfileListView(ListView):
    model = Post
    form_class = ProfileForm
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        self.username = get_object_or_404(
            User, username=self.kwargs['username']
        )
        return get_select_related().filter(
            author=self.username
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['profile'] = self.username
        return context


class CommentUpdateView(UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class CommentDeleteView(DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'comment_id'


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    paginate_by = 10

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


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        self.slug = get_object_or_404(
            Category, slug=self.kwargs['category_slug']
        )
        return get_select_related().filter(
            category=self.slug
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['post_list'] = self.slug
        context['category'] = self.slug
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        fields = form.save(commit=False)
        fields.author = User.objects.get(username=self.request.user)
        fields.save()
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create_post.html'

    def dispatch(self, request, *args, **kwargs):
        # Получаем объект по первичному ключу и автору или вызываем 404 ошибку.
        get_object_or_404(Post, pk=kwargs['pk'], author=request.user)
        # Если объект был найден, то вызываем родительский метод,
        # чтобы работа CBV продолжилась.
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:delete_post')
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        # Получаем объект по первичному ключу и автору или вызываем 404 ошибку.
        get_object_or_404(Post, pk=kwargs['post_id'], author=request.user)
        # Если объект был найден, то вызываем родительский метод,
        # чтобы работа CBV продолжилась.
        return super().dispatch(request, *args, **kwargs)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:index')


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST':
        if form.instance.author == request.user:
            if form.is_valid():
                form.save()
                return redirect('blog:post_detail', post_id)
        elif not request.user.is_authenticated:
            return redirect('blog:post_detail', post_id)
    context = {
        'post': post,
        'form': form
    }
    return render(request, 'blog/create.html', context)
