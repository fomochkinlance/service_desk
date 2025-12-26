from django.shortcuts import render, get_object_or_404, redirect
import json
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Document, Department, Comment, DocumentHistory
from .models import Attachment
from .forms import DocumentForm


def trigger_toast(response, message, level='success'):
    """Додає заголовок для HTMX, щоб показати повідомлення"""
    trigger_data = {'showMessage': {'message': message, 'level': level}}
    response['HX-Trigger'] = json.dumps(trigger_data)
    return response


@login_required
def incoming_list(request):
    documents = Document.objects.select_related('department').all()

    # --- Блок фільтрації (без змін) ---
    q = request.GET.get('q')
    if q:
        documents = documents.filter(
            Q(full_name__icontains=q) |
            Q(identifier__icontains=q) |
            Q(comment__icontains=q)
        )

    search_full_name = request.GET.get('search_full_name')
    if search_full_name:
        documents = documents.filter(full_name__icontains=search_full_name)

    search_identifier = request.GET.get('search_identifier')
    if search_identifier:
        documents = documents.filter(identifier__icontains=search_identifier)

    search_channel = request.GET.get('search_channel')
    if search_channel:
        documents = documents.filter(channel=search_channel)

    search_request_type = request.GET.get('search_request_type')
    if search_request_type:
        documents = documents.filter(request_type=search_request_type)

    search_department = request.GET.get('search_department')
    if search_department:
        documents = documents.filter(department_id=search_department)

    search_status = request.GET.get('search_status')
    if search_status:
        documents = documents.filter(status=search_status)

    search_created_at = request.GET.get('search_created_at')
    if search_created_at:
        documents = documents.filter(created_at__date=search_created_at)
    # ----------------------------------

    documents = documents.order_by('-created_at')

    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'documents': page_obj,
        'channel_choices': Document.CHANNELS,
        'type_choices': Document.TYPES,
        'status_choices': Document.STATUSES,
        'departments': Department.objects.all(),
    }

    if request.headers.get('HX-Request'):
        template = "documents/incoming_content.html"
    else:
        template = "documents/incoming_list.html"

    return render(request, template, context)

@login_required
def create_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.created_by = request.user
            doc.save()
            # ВИПРАВЛЕНО: Використовуємо redirect замість виклику функції
            return redirect('documents:incoming_list') 
    else:
        form = DocumentForm()
    
    return render(request, 'documents/partials/create_modal.html', {'form': form})

@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    # Завантажуємо коментарі
    comments = document.comments.select_related('user').order_by('-created_at')
    
    # Завантажуємо історію
    history = document.history.select_related('user').order_by('-created_at')

    context = {
        'document': document,
        'comments': comments,
        'history': history,
        'status_choices': Document.STATUSES,
        'departments': Department.objects.all(),
    }
    return render(request, "documents/document_detail_content.html", context)

@login_required
@require_POST
def update_status(request, pk):
    document = get_object_or_404(Document, pk=pk)
    new_status_code = request.POST.get('status')
    
    # За замовчуванням повідомлення про помилку або відсутність змін
    msg = "Статус не змінено"
    level = "error"

    if new_status_code and new_status_code != document.status and not document.is_closed:
        old_status_display = document.get_status_display()
        
        document.status = new_status_code
        document.save()
        
        new_status_display = document.get_status_display()
        
        DocumentHistory.objects.create(
            document=document,
            user=request.user,
            field_name="Статус",
            old_value=old_status_display,
            new_value=new_status_display
        )
        
        msg = f"Статус змінено на: {new_status_display}"
        level = "success"

    # Замість redirect викликаємо відображення сторінки
    response = document_detail(request, pk)
    return trigger_toast(response, msg, level)

@login_required
@require_POST
def update_department(request, pk):
    document = get_object_or_404(Document, pk=pk)
    dept_id = request.POST.get('department')
    
    msg = "Департамент не змінено"
    level = "error"

    if dept_id and not document.is_closed:
        if str(document.department_id) != str(dept_id):
            
            old_dept_name = document.department.name if document.department else "Не призначено"
            
            document.department_id = dept_id
            document.save()
            
            document.refresh_from_db()
            new_dept_name = document.department.name
            
            DocumentHistory.objects.create(
                document=document,
                user=request.user,
                field_name="Департамент",
                old_value=old_dept_name,
                new_value=new_dept_name
            )
            
            msg = f"Передано в департамент: {new_dept_name}"
            level = "success"

    # Викликаємо відображення та чіпляємо тост
    response = document_detail(request, pk)
    return trigger_toast(response, msg, level)

@login_required
def close_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        # Можна додати запис в історію про закриття тут, якщо потрібно
        document.is_closed = True
        document.status = 'closed' # Перевірте, чи такий код є у ваших STATUSES
        document.save()
    return redirect('documents:document_detail', pk=pk)

@login_required
def add_comment(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == "POST":
        text = request.POST.get('text')
        
        # Перевіряємо, чи є текст
        if text and text.strip():
            Comment.objects.create(
                document=document,
                user=request.user, 
                text=text
            )
            
            # Отримуємо оновлений список коментарів
            comments = document.comments.select_related('user').order_by('-created_at')
            
            # Рендеримо список
            response = render(request, "documents/partials/comments_list.html", {'comments': comments})
            
            # Чіпляємо повідомлення про успіх
            return trigger_toast(response, "Коментар додано")
        
        else:
            # Якщо текст порожній - повертаємо старий список (або нічого) і помилку
            comments = document.comments.select_related('user').order_by('-created_at')
            response = render(request, "documents/partials/comments_list.html", {'comments': comments})
            return trigger_toast(response, "Коментар не може бути порожнім", "error")
    
    # GET-запит (відкриття модалки)
    return render(request, "documents/partials/comment_modal.html", {'document': document})

@login_required
def document_files(request, pk):
    document = get_object_or_404(Document, pk=pk)
    files = document.attachments.select_related('uploaded_by').order_by('-uploaded_at')
    
    return render(request, 'documents/partials/files_list.html', {
        'document': document, 
        'files': files
    })

@login_required
@require_POST
def upload_file(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    if 'file' in request.FILES:
        file = request.FILES['file']
        Attachment.objects.create(
            document=document,
            file=file,
            uploaded_by=request.user,
            filename=file.name
        )
        # Оновлюємо список і кажемо "Успіх"
        response = document_files(request, pk)
        return trigger_toast(response, "Файл успішно завантажено")
    
    # Якщо помилка
    response = document_files(request, pk)
    return trigger_toast(response, "Помилка завантаження файлу", "error")

@login_required
@require_POST
def delete_file(request, pk):
    attachment = get_object_or_404(Attachment, pk=pk)
    doc_id = attachment.document.id # Запам'ятовуємо ID документа, щоб повернутися
    
    # Видаляємо
    attachment.file.delete()
    attachment.delete()
    
    # Повертаємо оновлений список
    response = document_files(request, doc_id)
    return trigger_toast(response, "Файл видалено")