from django.db import models


class PublishedModel(models.Model):
    """Абстрактная модель. Добвляет флаг is_published и значение created_at."""

    is_published = models.BooleanField(
        verbose_name='Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.',)
    created_at = models.DateTimeField(
        verbose_name='Добавлено',
        auto_now_add=True,)

    class Meta:
        abstract = True
