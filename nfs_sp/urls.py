from django.urls import path
from . import views

app_name = 'nfs_sp'

urlpatterns = [
    path('emitir/', views.emitir_nfs, name='emitir'),
    path('gerar-modelo/', views.gerar_modelo, name='gerar_modelo'),
    path('emitir-notas/', views.emitir_notas, name='emitir_notas'),
    path('excluir-notas/', views.excluir_notas, name='excluir_notas'),
    path('cancelar-notas/', views.cancelar_notas, name='cancelar_notas'),
    path('salvar-pdfs/', views.salvar_pdfs, name='salvar_pdfs'),
    path('detalhes-nota/<int:nota_id>/', views.detalhes_nota, name='detalhes_nota'),
    # NFTS
    path('gerar-modelo-nfts/', views.gerar_modelo_nfts, name='gerar_modelo_nfts'),
    path('emitir-nfts/', views.emitir_nfts, name='emitir_nfts'),
    path('excluir-nfts/', views.excluir_nfts, name='excluir_nfts'),
    path('cancelar-nfts/', views.cancelar_nfts, name='cancelar_nfts'),
    path('detalhes-nfts/<int:nota_id>/', views.detalhes_nfts, name='detalhes_nfts'),
]
