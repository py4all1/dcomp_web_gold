from django.urls import path
from . import views

app_name = 'nfse_nacional'

urlpatterns = [
    path('emitir/', views.emitir_nfse, name='emitir'),
    path('gerar-modelo/', views.gerar_modelo, name='gerar_modelo'),
    path('emitir-notas/', views.emitir_notas, name='emitir_notas'),
    path('excluir-notas/', views.excluir_notas, name='excluir_notas'),
    path('cancelar-notas/', views.cancelar_notas, name='cancelar_notas'),
    path('salvar-pdfs/', views.salvar_pdfs, name='salvar_pdfs'),
    path('detalhes-nota/<int:nota_id>/', views.detalhes_nota, name='detalhes_nota'),
    path('editar-nota/<int:nota_id>/', views.editar_nota, name='editar_nota'),
]
