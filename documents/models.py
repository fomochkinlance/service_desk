# documents/models.py
from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField("Назва департаменту", max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    
    CHANNELS = [
        ('phone', 'Телефон'),
        ('email', 'Email'),
        ('chat', 'Чат бот'),
        ('telegram', 'Telegram'),
        ('viber', 'Viber'),
    ]

    TYPES = [
        ('bug', 'Помилка ПЗ'),
        ('feature', 'Новий функціонал'),
        ('question', 'Консультація'),
        ('access', 'Надання доступу'),
        ('complaint', 'Скарга'),
    ]

    STATUSES = [
        ('new', 'Новий'),
        ('in_progress', 'В роботі'),
        ('pending', 'Очікування'),
        ('resolved', 'Вирішено'),
        ('closed', 'Зачинено'),
    ]

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Створив")
    identifier = models.CharField("Ідентифікатор", max_length=12)
    created_at = models.DateTimeField("Дата створення", auto_now_add=True)
    updated_at = models.DateTimeField("Дата зміни", auto_now=True)

    full_name = models.CharField("ПІБ", max_length=100)
    channel = models.CharField("Канал зв'язку", max_length=20, choices=CHANNELS)
    request_type = models.CharField("Тип звернення", max_length=20, choices=TYPES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name="Департамент")
    status = models.CharField("Статус", max_length=20, choices=STATUSES, default='new')
    comment = models.TextField("Коментар", blank=True)
    file = models.FileField("Файл", upload_to='uploads/documents/', blank=True, null=True)
    is_closed = models.BooleanField("Закрита", default=False)

    def __str__(self):
        return f"Заявка № {self.id}"

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.identifier} - {self.full_name}"
    
class Comment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField("Коментар")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Коментар від {self.user} до {self.document}"
    

class DocumentHistory(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Тип зміни (status або department)
    field_name = models.CharField(max_length=50) 
    
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']