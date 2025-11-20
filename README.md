# Tax Gold - Sistema de Emissão de Notas Fiscais

Sistema completo para emissão de notas fiscais de serviço desenvolvido em Django.

## 🚀 Funcionalidades

- **Tela Inicial**: Apresentação do sistema com informações úteis e logo da empresa
- **Menu Lateral Animado**: Navegação intuitiva com animações suaves
- **Sistema de Autenticação**: Integrado com o app `accounts` para controle de usuários e empresas
- **Emissão de Notas Fiscais**:
  - NFS-e São Paulo
  - NFT-e São Paulo
  - NFS-e Nacional
- **Tema Claro/Escuro**: Alternância entre temas com persistência da preferência do usuário
- **Design Responsivo**: Interface adaptável para desktop e mobile

## 📋 Pré-requisitos

- Python 3.8+
- pip
- virtualenv (recomendado)

## 🔧 Instalação

1. **Clone o repositório** (se ainda não tiver):
```bash
git clone <url-do-repositorio>
cd emissor_gold_web
```

2. **Crie e ative o ambiente virtual**:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

4. **Execute as migrações**:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crie um superusuário**:
```bash
python manage.py createsuperuser
```

6. **Colete os arquivos estáticos**:
```bash
python manage.py collectstatic --noinput
```

7. **Inicie o servidor de desenvolvimento**:
```bash
python manage.py runserver
```

8. **Acesse o sistema**:
   - Sistema: http://localhost:8000/
   - Admin: http://localhost:8000/admin/

## 📁 Estrutura do Projeto

```
emissor_gold_web/
├── accounts/              # App de autenticação e usuários
├── core/                  # App principal (home, cadastro, ajuda)
├── nfs_sp/               # Emissão NFS-e São Paulo
├── nfts_sp/              # Emissão NFT-e São Paulo
├── nfse_nacional/        # Emissão NFS-e Nacional
├── emissor_gold/         # Configurações do projeto
├── static/               # Arquivos estáticos (CSS, JS, imagens)
│   ├── css/
│   └── js/
├── templates/            # Templates HTML
│   ├── base.html
│   ├── core/
│   ├── nfs_sp/
│   ├── nfts_sp/
│   └── nfse_nacional/
├── logos/                # Logos da empresa
├── manage.py
└── requirements.txt
```

## 🎨 Recursos de Interface

### Menu Lateral
- Navegação com ícones e textos
- Animação de expansão/colapso
- Indicador de página ativa
- Responsivo para mobile

### Sistema de Temas
- **Tema Claro**: Interface clara e moderna
- **Tema Escuro**: Reduz fadiga visual
- Persistência da preferência no localStorage
- Transições suaves entre temas

### Componentes
- Cards informativos
- Formulários estilizados
- Alertas e mensagens
- Botões com animações
- Dropdown de usuário

## 🔐 Sistema de Autenticação

O sistema utiliza o app `accounts` que já está configurado com:
- Modelo `EmpresaContratante`: Gerencia empresas que contratam o sistema
- Modelo `UserProfile`: Perfil de usuário vinculado a uma empresa
- Validação de CNPJ/CPF
- Sistema de planos e status
- Controle de limite de usuários por empresa

## 🛠️ Tecnologias Utilizadas

- **Backend**: Django 4.2
- **Frontend**: 
  - Bootstrap 5.3
  - Bootstrap Icons
  - JavaScript (Vanilla)
- **Database**: SQLite (desenvolvimento)
- **Estilização**: CSS3 com variáveis CSS

## 📝 Próximos Passos

- [ ] Implementar lógica de emissão de notas fiscais
- [ ] Integração com APIs das prefeituras
- [ ] Sistema de relatórios
- [ ] Histórico de notas emitidas
- [ ] Exportação de dados (PDF, XML)
- [ ] Sistema de notificações
- [ ] Backup automático

## 👥 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é proprietário e confidencial.

## 📞 Suporte

Para suporte, entre em contato:
- Email: suporte@emissorgold.com.br
- Telefone: (11) 1234-5678
- WhatsApp: (11) 98765-4321