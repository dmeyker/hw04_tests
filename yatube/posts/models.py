from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model

# Автоматически создаем таблицу для пользователя
User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Укажите название группы'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Уникальный адрес группы',
        help_text='Выберите из списка или укажите новый адрес'
    )
    description = models.TextField(
        verbose_name='Описание сообщества',
        help_text='Добавьте описание группы'
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Добавьте описание поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста',
        help_text='Выберите автора поста'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Укажите группу, в которой опубликуется пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Пост"

    def __str__(self) -> str:
        return self.text[:15]
