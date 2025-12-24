
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home_view(request):
    return render(request, 'accounts/home.html', {
        'user': request.user,
    })