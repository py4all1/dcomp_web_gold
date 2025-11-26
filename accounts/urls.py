from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import EmpresaAuthForm
from . import views
from . import views_admin

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=EmpresaAuthForm,
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    
    # Admin - Gerenciamento de Empresas (apenas superuser)
    path('admin/empresas/', views_admin.admin_empresas, name='admin_empresas'),
    path('admin/empresas/<int:empresa_id>/', views_admin.admin_empresa_detalhes, name='admin_empresa_detalhes'),
    path('admin/empresas/<int:empresa_id>/toggle/', views_admin.admin_empresa_toggle_status, name='admin_empresa_toggle_status'),
    path('admin/empresas/<int:empresa_id>/editar/', views_admin.admin_empresa_editar, name='admin_empresa_editar'),
    path('admin/empresas/<int:empresa_id>/renovar/', views_admin.admin_empresa_renovar, name='admin_empresa_renovar'),
]
