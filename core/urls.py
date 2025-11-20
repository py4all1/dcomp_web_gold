from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('cadastro/editar/<int:empresa_id>/', views.editar_empresa, name='editar_empresa'),
    path('cadastro/excluir/<int:empresa_id>/', views.excluir_empresa, name='excluir_empresa'),
    path('ajuda/', views.ajuda, name='ajuda'),
]
