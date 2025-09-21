# Projeto BellCílios Academy

Sistema web de agendamento desenvolvido em **Python (Django)** e **MySQL**.

## Funcionalidades
- Cadastro de clientes e serviços
- Upload de imagens
- Calendário interativo (FullCalendar)
- Painel administrativo protegido

## Tecnologias
- Python 3 / Django
- MySQL
- HTML / CSS / JavaScript
- Bootstrap
- Deploy no DigitalOcean (Ubuntu 22.04)

## Demonstração
🔗 [Acesse o projeto online](https://bellciliosacademy.com.br)

![screenshot]()


## Como rodar localmente
```bash
git clone https://github.com/robertsouzadev/bellcilios
cd bellcilios
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
