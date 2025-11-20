# 🚀 Guia de Início Rápido - Tax Gold

## Passos para Executar o Projeto

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar Migrações do Banco de Dados
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Criar Superusuário (Admin)
```bash
python manage.py createsuperuser
```
Siga as instruções e crie um usuário administrador.

### 4. Criar uma Empresa Contratante (via Admin)
1. Inicie o servidor: `python manage.py runserver`
2. Acesse: http://localhost:8000/admin/
3. Faça login com o superusuário criado
4. Vá em "Empresas Contratantes" e clique em "Adicionar"
5. Preencha os dados:
   - CNPJ/CPF
   - Razão Social/Nome
   - Configure os limites e plano
6. Salve a empresa

### 5. Vincular Usuário à Empresa
1. No admin, vá em "Perfis de Usuários"
2. Encontre o perfil do seu usuário
3. Selecione a empresa criada no campo "Empresa"
4. Preencha os outros campos (Nome, Telefone)
5. Salve

### 6. Acessar o Sistema
1. Faça logout do admin
2. Acesse: http://localhost:8000/
3. Faça login com suas credenciais
4. Você verá a tela inicial do Tax Gold!

## 📋 Estrutura de Navegação

- **Início**: Tela principal com cards de ações rápidas
- **Cadastro**: Gerenciamento de empresas e dados
- **Emitir NFS-SP**: Formulário para emissão de NFS-e São Paulo
- **Emitir NFTS-SP**: Formulário para emissão de NFT-e São Paulo
- **Emitir NFSE Nacional**: Formulário para emissão de NFS-e Nacional
- **Ajuda**: Central de ajuda e suporte

## 🎨 Funcionalidades Implementadas

### ✅ Menu Lateral Animado
- Clique no ícone de menu (☰) para expandir/colapsar
- Em mobile, o menu aparece como overlay
- Estado do menu é salvo no navegador

### ✅ Tema Claro/Escuro
- Clique no ícone de sol/lua no canto superior direito
- Tema é salvo automaticamente
- Transições suaves entre temas

### ✅ Sistema de Autenticação
- Login/Logout integrado
- Controle de acesso por empresa
- Perfil de usuário

## 🔧 Comandos Úteis

### Iniciar servidor de desenvolvimento
```bash
python manage.py runserver
```

### Criar novas migrações
```bash
python manage.py makemigrations
```

### Aplicar migrações
```bash
python manage.py migrate
```

### Criar superusuário
```bash
python manage.py createsuperuser
```

### Coletar arquivos estáticos (produção)
```bash
python manage.py collectstatic
```

### Abrir shell do Django
```bash
python manage.py shell
```

## 📝 Notas Importantes

1. **Logos**: Coloque os logos da empresa na pasta `static/images/` ou `logos/`
   - `logo.png` - Logo pequeno para o menu lateral
   - `logo-large.png` - Logo grande para a tela inicial

2. **Email**: O sistema tem referência a um módulo `email_` no arquivo `accounts/views.py`. 
   Você pode comentar essa parte se não tiver configurado o envio de emails ainda.

3. **Desenvolvimento**: As funcionalidades de emissão de notas estão com formulários prontos,
   mas a lógica de integração com as APIs das prefeituras precisa ser implementada.

## 🐛 Troubleshooting

### Erro: "No module named 'email_'"
Comente as linhas 13 e 22-29 em `accounts/views.py` se não tiver o módulo de email configurado.

### Erro: "Table doesn't exist"
Execute as migrações: `python manage.py migrate`

### Erro: "Static files not found"
Execute: `python manage.py collectstatic`

### Menu não aparece em mobile
Verifique se o JavaScript está carregando corretamente no navegador (F12 > Console)

## 🎯 Próximos Passos de Desenvolvimento

1. Implementar lógica de emissão de notas fiscais
2. Integrar com APIs das prefeituras (SP, Nacional)
3. Criar sistema de histórico de notas
4. Adicionar validações nos formulários
5. Implementar exportação de PDF/XML
6. Criar dashboard com estatísticas
7. Adicionar sistema de notificações

## 📞 Suporte

Se tiver dúvidas ou problemas, consulte o README.md principal ou entre em contato com a equipe de desenvolvimento.
