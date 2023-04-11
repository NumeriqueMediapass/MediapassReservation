from django.db.models import Q
from django.shortcuts import render

from shop.models import Product


def index(request):
    return render(request, 'home/index.html')


def handler404(request, exception):
    return render(request, 'home/404.html', status=404)


def search(request):
    query = request.GET.get('q')
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        results = []
    return render(request, 'home/search.html', {'results': results})


def legal_information(request):
    return render(request, 'home/legalinformation.html')