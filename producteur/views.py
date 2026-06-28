from django.shortcuts import render

# Create your views here.

def inscription_producteur(request):
    return render(request,'inscription.html')