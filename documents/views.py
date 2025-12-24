from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
# Переконайтеся, що всі моделі імпортовані
from .models import Document, Department, Comment, DocumentHistory
from .forms import DocumentForm

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
    print("--- ЗАПИТ НА ЗМІНУ СТАТУСУ ---")
    document = get_object_or_404(Document, pk=pk)
    new_status_code = request.POST.get('status')
    
    # Перевірка, чи статус дійсно змінився і документ не закритий
    if new_status_code and new_status_code != document.status and not document.is_closed:
        old_status_display = document.get_status_display()
        
        document.status = new_status_code
        document.save()
        
        # Отримуємо нове відображення статусу
        new_status_display = document.get_status_display()
        
        # Створюємо запис в історії
        DocumentHistory.objects.create(
            document=document,
            user=request.user,
            field_name="Статус",
            old_value=old_status_display,
            new_value=new_status_display
        )
        print("Статус оновлено та записано в історію")
    
    # ВИПРАВЛЕНО: Redirect замість render (Pattern PRG)
    # Переконайтеся, що 'documents:document_detail' відповідає вашому urls.py
    return redirect('documents:document_detail', pk=pk)

@login_required
@require_POST
def update_department(request, pk):
    document = get_object_or_404(Document, pk=pk)
    dept_id = request.POST.get('department')
    
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

    # ВИПРАВЛЕНО: Redirect
    return redirect('documents:document_detail', pk=pk)

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
        if text:
            Comment.objects.create(
                document=document,
                user=request.user, 
                text=text
            )
            # Тут можна залишити render, якщо це AJAX/HTMX запит на оновлення списку коментарів
            comments = document.comments.select_related('user').order_by('-created_at')
            return render(request, "documents/partials/comments_list.html", {'comments': comments})
    
    return render(request, "documents/partials/comment_modal.html", {'document': document})