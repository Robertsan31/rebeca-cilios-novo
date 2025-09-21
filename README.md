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

![screenshot](<img width="1792" height="1120" alt="Captura de Tela 2025-09-21 às 20 21 18" src="https://github.com/user-attachments/assets/ff2a2859-ba8c-4993-8eae-5603416488ad" />
)![Uploading Captura de Tela 2025-09-21 às 20.21.18.png…]()


## Como rodar localmente
```bash
git clone https://github.com/robertsouzadev/bellcilios
cd bellcilios
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
