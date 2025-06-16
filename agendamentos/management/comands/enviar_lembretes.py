# agendamentos/management/commands/enviar_lembretes.py

import pytz
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from agendamentos.models import Agendamento
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Envia e-mails de lembrete para agendamentos que acontecerão em breve.'

    def handle(self, *args, **options):
        # Define o fuso horário correto
        timezone = pytz.timezone(settings.TIME_ZONE)
        agora = datetime.now(timezone)

        # Define o intervalo de tempo para os lembretes (ex: nas próximas 2 horas)
        inicio_intervalo = agora + timedelta(minutes=59)
        fim_intervalo = agora + timedelta(minutes=61) # Uma janela de 2 minutos para pegar agendamentos "às 10:00"

        # Filtra os agendamentos que estão dentro do intervalo e ainda não tiveram lembrete enviado
        agendamentos_proximos = Agendamento.objects.filter(
            data_hora__gte=inicio_intervalo,
            data_hora__lte=fim_intervalo,
            status='Confirmado',
            lembrete_enviado=False # Adicionaremos este campo ao modelo
        )

        self.stdout.write(f"Verificando agendamentos entre {inicio_intervalo.strftime('%H:%M')} e {fim_intervalo.strftime('%H:%M')}")

        if not agendamentos_proximos:
            self.stdout.write(self.style.SUCCESS('Nenhum agendamento próximo para notificar.'))
            return

        for agendamento in agendamentos_proximos:
            assunto = f"Lembrete de Agendamento - {agendamento.servico.nome}"
            data_formatada = agendamento.data_hora.strftime('%d/%m/%Y às %H:%M')
            
            # E-mail para a cliente
            mensagem_cliente = (
                f"Olá, {agendamento.cliente.nome}!\n\n"
                f"Este é um lembrete do seu agendamento na BellCilios.\n\n"
                f"Serviço: {agendamento.servico.nome}\n"
                f"Data e Hora: {data_formatada}\n\n"
                f"Estamos te esperando!\n"
                f"Atenciosamente, Equipe BellCilios"
            )
            send_mail(
                assunto,
                mensagem_cliente,
                settings.DEFAULT_FROM_EMAIL,
                [agendamento.cliente.email],
                fail_silently=False
            )

            # E-mail para a dona (Rebeca)
            mensagem_dono = (
                f"Lembrete: O agendamento de {agendamento.cliente.nome} "
                f"para o serviço '{agendamento.servico.nome}' começará em aproximadamente 1 hora ({data_formatada})."
            )
            send_mail(
                f"Lembrete: {agendamento.servico.nome} às {agendamento.data_hora.strftime('%H:%M')}",
                mensagem_dono,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False
            )

            # Marca o agendamento para não enviar o lembrete de novo
            agendamento.lembrete_enviado = True
            agendamento.save()

            self.stdout.write(self.style.SUCCESS(f'Lembrete enviado para o agendamento de {agendamento.cliente.nome}'))

