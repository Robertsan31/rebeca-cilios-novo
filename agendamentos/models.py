# agendamentos/models.py
from django.db import models
from django.core.exceptions import ValidationError
from PIL import Image
import re

def validate_cpf(value: str):
    if not re.match(r'^\d{11}$', value or ''):
        raise ValidationError('CPF inválido. Deve conter 11 dígitos numéricos.')

def validate_telefone(value: str):
    """
    Aceita vazio (blank=True no campo). Se vier algo, valida somente números após
    remover + - ( ) e espaços.
    """
    if value in (None, ''):
        return
    cleaned_value = re.sub(r'[\s\+\-\(\)]', '', value)
    if not cleaned_value.isdigit():
        raise ValidationError('Telefone inválido. Use apenas números (pode conter +, -, (, ) e espaços).')

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True, error_messages={'unique': "Este e-mail já está cadastrado."})
    telefone = models.CharField(max_length=20, blank=True, validators=[validate_telefone])
    cpf = models.CharField(
        max_length=11,
        unique=True,
        validators=[validate_cpf],
        help_text="Digite apenas os 11 números do CPF.",
        error_messages={'unique': "Este CPF já está cadastrado."}
    )
    data_cadastro = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.nome

class Servico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    imagem = models.ImageField(upload_to='servicos/', blank=True, null=True, verbose_name="Imagem do Serviço")
    duracao = models.IntegerField(default=60, help_text="Duração do serviço em minutos")

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        """
        Salva normalmente e, se houver imagem, garante recorte/resize 400x400.
        (Não conflita com o recorte 1200x1200 feito na view — apenas downsizing
        se você editar via admin sem recortar.)
        """
        super().save(*args, **kwargs)
        if self.imagem:
            try:
                img_path = self.imagem.path
                with Image.open(img_path) as img:
                    # Garante quadrado (corte central) e 400x400
                    w, h = img.size
                    if w != h:
                        side = min(w, h)
                        left = (w - side) // 2
                        top = (h - side) // 2
                        img = img.crop((left, top, left + side, top + side))
                    if img.size != (400, 400):
                        img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    img.save(img_path, quality=90, optimize=True)
            except Exception as e:
                # Evita quebrar o fluxo por erro de Pillow
                print(f"[SERVICO.save] Erro ao processar imagem: {e}")

class Agendamento(models.Model):
    STATUS_CHOICES = [
        ('Confirmado', 'Confirmado'),
        ('Pendente', 'Pendente'),
        ('Cancelado', 'Cancelado'),
        ('Realizado', 'Realizado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.SET_NULL, null=True, related_name='agendamentos')
    data_hora = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmado')
    lembrete_enviado = models.BooleanField(default=False)

    class Meta:
        ordering = ['data_hora']

    def __str__(self) -> str:
        nome_serv = self.servico.nome if self.servico else "Serviço Removido"
        nome_cli = self.cliente.nome if self.cliente else "Cliente"
        return f'{nome_serv} para {nome_cli} em {self.data_hora.strftime("%d/%m/%Y %H:%M")}'
