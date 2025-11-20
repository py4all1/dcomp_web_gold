from django import forms
from .models import Empresa
import re


class EmpresaCadastroForm(forms.ModelForm):
    """Formulário para cadastro de empresas emissoras com certificado digital"""
    
    certificado_pfx = forms.FileField(
        label='Certificado Digital (PFX/P12)',
        required=False,
        help_text='Selecione o arquivo do certificado digital (.pfx ou .p12)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pfx,.p12'
        })
    )
    
    class Meta:
        model = Empresa
        fields = ['cnpj', 'razao_social', 'nome_fantasia', 'inscricao_municipal', 
                  'inscricao_estadual', 'senha_certificado', 'tem_procurador', 'cpf_cnpj_procurador']
        widgets = {
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00',
                'maxlength': '18'
            }),
            'razao_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razão Social da Empresa'
            }),
            'nome_fantasia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome Fantasia (opcional)'
            }),
            'inscricao_municipal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inscrição Municipal'
            }),
            'inscricao_estadual': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inscrição Estadual (opcional)'
            }),
            'senha_certificado': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Senha do Certificado Digital'
            }),
            'tem_procurador': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_tem_procurador'
            }),
            'cpf_cnpj_procurador': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CPF ou CNPJ do Procurador',
                'maxlength': '18',
                'id': 'id_cpf_cnpj_procurador'
            }),
        }
        labels = {
            'cnpj': 'CNPJ',
            'razao_social': 'Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'inscricao_municipal': 'Inscrição Municipal',
            'inscricao_estadual': 'Inscrição Estadual',
            'senha_certificado': 'Senha do Certificado',
            'tem_procurador': 'Possui Procurador',
            'cpf_cnpj_procurador': 'CPF/CNPJ do Procurador',
        }
    
    def clean_cnpj(self):
        """Remove formatação do CNPJ"""
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Remove caracteres não numéricos
            cnpj = re.sub(r'\D', '', cnpj)
        return cnpj
    
    def clean_cpf_cnpj_procurador(self):
        """Remove formatação do CPF/CNPJ do procurador"""
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj_procurador')
        if cpf_cnpj:
            # Remove caracteres não numéricos
            cpf_cnpj = re.sub(r'\D', '', cpf_cnpj)
        return cpf_cnpj
    
    def clean_certificado_pfx(self):
        """Valida o arquivo do certificado"""
        arquivo = self.cleaned_data.get('certificado_pfx')
        if arquivo:
            # Verifica extensão
            nome = arquivo.name.lower()
            if not (nome.endswith('.pfx') or nome.endswith('.p12')):
                raise forms.ValidationError('O arquivo deve ser .pfx ou .p12')
            
            # Verifica tamanho (máximo 5MB)
            if arquivo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('O arquivo não pode ser maior que 5MB')
        
        return arquivo
    
    def clean(self):
        """Validação customizada"""
        cleaned_data = super().clean()
        tem_procurador = cleaned_data.get('tem_procurador')
        cpf_cnpj_procurador = cleaned_data.get('cpf_cnpj_procurador')
        
        # Se marcou procurador, CPF/CNPJ é obrigatório
        if tem_procurador and not cpf_cnpj_procurador:
            raise forms.ValidationError('Informe o CPF ou CNPJ do procurador.')
        
        return cleaned_data
