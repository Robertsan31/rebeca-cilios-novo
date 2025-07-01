# agendamentos/models.py
from django.db import models
from django.core.exceptions import ValidationError
import re

def validate_cpf(value):
    """
    Validador customizado para o formato do CPF (apenas números).
    """
    if not re.match(r'^\d{11}$', value):
        raise ValidationError('CPF inválido. Deve conter 11 dígitos numéricos.')

def validate_telefone(value):
    """
    Validador customizado para o formato do Telefone.
    Permite apenas números e os caracteres +, -, (, ), e espaço.
    """
    cleaned_value = re.sub(r'[\s\+\-\(\)]', '', value)
    if not cleaned_value.isdigit():
        raise ValidationError('Telefone inválido. Utilize apenas números e os caracteres +, -, (, ).')

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(
        unique=True,
        error_messages={'unique': "Este e-mail já está cadastrado."}
    )
    telefone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[validate_telefone]
    )
    cpf = models.CharField(
        max_length=11, 
        unique=True, 
        validators=[validate_cpf],
        help_text="Digite apenas os 11 números do CPF.",
        error_messages={'unique': "Este CPF já está cadastrado."}
    )

    def __str__(self):
        return self.nome

class Servico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)

    imagem = models.ImageField(upload_to='servicos/', blank=True, null=True, verbose_name="Imagem do Serviço")

    def __str__(self):
        return self.nome

class Agendamento(models.Model):
    STATUS_CHOICES = [
        ('Confirmado', 'Confirmado'),
        ('Pendente', 'Pendente'),
        ('Cancelado', 'Cancelado'),
        ('Realizado', 'Realizado'), 
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.SET_NULL, null=True, related_name='agendamentos')
    # CORREÇÃO: Removido o 'unique=True' para permitir reutilizar horários cancelados
    data_hora = models.DateTimeField() 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmado')
    
    lembrete_enviado = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.servico.nome if self.servico else "Serviço Removido"} para {self.cliente.nome} em {self.data_hora.strftime("%d/%m/%Y %H:%M")}'

    class Meta:
        ordering = ['data_hora']
