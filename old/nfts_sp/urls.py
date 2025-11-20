from django.urls import path
from . import views

app_name = 'nfts_sp'

urlpatterns = [
    path('emitir/', views.emitir_nfts, name='emitir'),
]
