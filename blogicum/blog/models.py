from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()
TITLE_LIMIT = 30


class PublishedAndCreatedField(models.Model):
    """Абстрактная модель."""

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        'Добавлено',
        auto_now_add=True
    )

    class Meta:
        abstract = True


class Category(PublishedAndCreatedField):
    """Модель категорий."""

    title = models.CharField(
        'Заголовок',
        max_length=256
    )
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL;'
            ' разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:TITLE_LIMIT]


class Location(PublishedAndCreatedField):
    """Модель локации."""

    name = models.CharField('Название места', max_length=256)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:TITLE_LIMIT]


class Post(PublishedAndCreatedField):
    """Модель постов связанный с моделями Location и Category."""

    title = models.CharField(
        'Заголовок',
        max_length=256
    )
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем'
            ' — можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Местоположение',
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    image = models.ImageField(
        'Фото',
        blank=True,
        upload_to='posts_images'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'

    def get_absolute_url(self):
        '''С помощью функции reverse() возвращаем URL объекта.'''
        return reverse('blog:post_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title[:TITLE_LIMIT]


class Comment(models.Model):
    ''''Модель коментариев связанная с моделью Post'''

    text = models.TextField('Текст коментария', blank=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор публикации'
    )

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return self.title
