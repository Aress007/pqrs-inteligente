from django.shortcuts import render
from django.views.decorators.cache import never_cache

@never_cache
def inicio(request):
    return render(request, 'core/inicio.html')