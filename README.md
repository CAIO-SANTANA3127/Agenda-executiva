<div align="center">

# 📅 Agenda Executiva

### Sistema de Gestão de Reuniões com Confirmação Automática via WhatsApp

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?logo=whatsapp)](https://evolution-api.com/)

Sistema completo para gestão de reuniões executivas com integração WhatsApp (Evolution API), análise inteligente de respostas, calendário interativo e disparador automático de aniversários.

[Instalação](#-instalação-rápida) • [Configuração](#%EF%B8%8F-configuração) • [Uso](#-uso-básico) • [API](#-endpoints-principais)

</div>

---

## ✨ Principais Funcionalidades

- 🤖 **Confirmação Automática via WhatsApp** - Envia mensagem ao criar reunião
- 🧠 **Análise Inteligente de Respostas** - Detecta confirmação, recusa ou dúvida automaticamente
- 📊 **Dashboard com Estatísticas** - Métricas em tempo real
- 🎂 **Sistema de Aniversários** - Disparos automáticos programados
- 📆 **Calendário Completo** - Eventos, reuniões, feriados e aniversários
- ⚡ **Detecção de Conflitos** - Alerta de horários duplicados

---

## 🛠️ Stack Tecnológico

**Backend:** Python 3.8+ • Flask • SQLite • Evolution API  
**Frontend:** HTML5 • CSS3 • JavaScript • Bootstrap • Font Awesome

---

## 📋 Pré-requisitos

- Python 3.8+
- Evolution API configurada
- IP público ou ngrok

---

## 🚀 Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/CAIO-SANTANA3127/Agenda-executiva.git
cd Agenda-executiva

# Crie ambiente virtual (opcional mas recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instale dependências
pip install -r requirements.txt

# Execute
python app.py
```

## 💡 Uso Básico

**Criar Reunião com Confirmação Automática:**
1. Acesse Agenda → Nova Reunião
2. Preencha: Nome, Telefone (5521999999999), Data/Hora, Assunto
3. Marque: "Enviar confirmação automática via WhatsApp"
4. Salvar → Mensagem enviada automaticamente!

**Sistema reconhece automaticamente:**
- ✅ Confirmações: "sim", "ok", "confirmo", "vou", 👍
- ❌ Recusas: "não", "não posso", "cancelar", 👎
- ❓ Dúvidas: "talvez", "verificar", 🤔

**Sistema de Aniversários:**
1. Prepare Excel com: NOME, EMPRESA, NASCIMENTO, WHATSAPP
2. Acesse: Menu → Disparador → Sincronizar Planilha
3. Configure horário → Envios automáticos!

---

## 🌐 Endpoints Principais

```http
# Reuniões
GET/POST   /api/reunioes              # Listar/Criar
PUT/DELETE /agenda/editar/<id>        # Editar/Excluir
GET        /api/meetings/<id>/status  # Status

# WhatsApp
POST /whatsapp/send-message           # Enviar mensagem
GET  /whatsapp/monitoring-status      # Status monitoramento
POST /whatsapp/force-monitor-all      # Forçar monitoramento
POST /webhook/evolution               # Webhook Evolution API

# Eventos & Aniversários
GET/POST   /api/eventos/list          # Listar/Criar eventos
POST       /api/aniversarios/sync-spreadsheet  # Sincronizar
```

---

## 🐛 Troubleshooting


### Logs Esperados ao Receber Mensagem

```
📥 Processando webhook...
📱 De: 5521999999999@s.whatsapp.net
💬 Texto: sim, confirmo a reunião
🔄 Normalizando número...
🎯 MATCH! Reunião encontrada: ID 123
📊 Status detectado: confirmed (confiança: 0.95)
💾 Resposta salva no banco
✅ Reunião #123 atualizada para: confirmed
```


## 📈 Roadmap

### 🎯 Próximas Funcionalidades

- [ ] 📧 Integração com e-mail (Gmail/Outlook)
- [ ] 📊 Relatórios em PDF exportáveis
- [ ] 🔔 Notificações push no navegador
- [ ] 🌐 API REST completa documentada (Swagger)
- [ ] 👥 Sistema multi-usuário com permissões
- [ ] 📱 App mobile (React Native)
- [ ] 🤖 Chatbot inteligente para agendamento
- [ ] 📅 Integração com Google Calendar
- [ ] 💳 Sistema de cobrança de reuniões
- [ ] 🎨 Temas personalizáveis

### 🐛 Melhorias Planejadas

- [ ] Otimização de queries SQL
- [ ] Cache Redis para melhor performance
- [ ] Testes automatizados (pytest)
- [ ] CI/CD com GitHub Actions
- [ ] Docker Compose para deploy fácil
- [ ] Documentação interativa (MkDocs)

---

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! 🎉

### Como Contribuir

1. **Fork** este repositório
2. Crie uma **branch** para sua feature:
   ```bash
   git checkout -b feature/minha-nova-funcionalidade
   ```
3. **Commit** suas mudanças:
   ```bash
   git commit -m 'feat: Adiciona nova funcionalidade X'
   ```
4. **Push** para a branch:
   ```bash
   git push origin feature/minha-nova-funcionalidade
   ```
5. Abra um **Pull Request**

### 📝 Padrão de Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação
- `refactor:` Refatoração de código
- `test:` Testes
- `chore:` Tarefas gerais

### 🐛 Reportar Bugs

Abra uma [issue](https://github.com/CAIO-SANTANA3127/Agenda-executiva/issues) com:

- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Screenshots (se aplicável)
- Versão do Python e sistema operacional

---

## 📝 Changelog

### 🎉 v1.0.0 (Dezembro 2024)

**Funcionalidades Principais:**
- ✨ Sistema completo de gestão de reuniões
- 💬 Integração WhatsApp via Evolution API
- 🤖 Análise inteligente de respostas com IA
- 🎂 Sistema automático de aniversários
- 📆 Calendário interativo com eventos
- 🔍 Autocomplete inteligente de clientes
- 📊 Dashboard com estatísticas em tempo real
- 🔔 Detecção automática de conflitos
- 📱 Interface responsiva e moderna

**Tecnologias:**
- Python 3.8+
- Flask 2.0+
- SQLite
- Evolution API
- JavaScript ES6+

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

```
MIT License

Copyright (c) 2024 Caio Santana

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 👤 Autor

<div align="center">

### Caio Santana

[![GitHub](https://img.shields.io/badge/GitHub-CAIO--SANTANA3127-181717?logo=github)](https://github.com/CAIO-SANTANA3127)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Caio%20Santana-0077B5?logo=linkedin)](https://linkedin.com/in/seu-perfil)
[![Email](https://img.shields.io/badge/Email-caiosantana3127@gmail.com-D14836?logo=gmail)](mailto:caiosantana3127@gmail.com)

**Desenvolvedor Full Stack | Sistemas de Informação**

🏢 2D Consultores - Business Intelligence & Web Development

</div>

---

## 🙏 Agradecimentos

Agradecimentos especiais a:

- 🚀 [**Evolution API**](https://evolution-api.com/) - Pela excelente API de WhatsApp
- 🐍 [**Flask**](https://flask.palletsprojects.com/) - Framework web poderoso e flexível
- 🎨 [**Font Awesome**](https://fontawesome.com/) - Ícones incríveis
- 📚 [**Bootstrap**](https://getbootstrap.com/) - Framework CSS responsivo
- 🐼 [**Pandas**](https://pandas.pydata.org/) - Manipulação de dados
- 💼 **2D Consultores** - Pelo apoio e oportunidade de desenvolvimento

---

## 📞 Suporte

Precisa de ajuda? Entre em contato:

- 📧 **Email:** caiosantana3127@gmail.com
- 💬 **Issues:** [GitHub Issues](https://github.com/CAIO-SANTANA3127/Agenda-executiva/issues)
- 📱 **WhatsApp:** [Clique aqui](https://wa.me/5521999999999)

---

## ⭐ Star History

Se este projeto foi útil para você, considere dar uma ⭐!

[![Star History Chart](https://api.star-history.com/svg?repos=CAIO-SANTANA3127/Agenda-executiva&type=Date)](https://star-history.com/#CAIO-SANTANA3127/Agenda-executiva&Date)

---

<div align="center">

### 💡 Desenvolvido com ❤️ para otimizar a gestão de reuniões executivas

**[⬆ Voltar ao topo](#-agenda-executiva)**

---

**© 2024 Caio Santana | 2D Consultores**

![Made with Love](https://img.shields.io/badge/Made%20with-❤-red)
![Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)
![Flask](https://img.shields.io/badge/Made%20with-Flask-green?logo=flask)

</div>


