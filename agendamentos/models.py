from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from PIL import Image
import re


# ============================
# VALIDADORES
# ============================

def validate_cpf(value: str):
    if not value:
        return
    if not re.match(r'^\d{11}$', value):
        raise ValidationError('CPF inválido. Deve conter 11 dígitos numéricos.')


def validate_telefone(value: str):
    if value in (None, ''):
        return
    cleaned_value = re.sub(r'[\s\+\-\(\)]', '', value)
    if not cleaned_value.isdigit():
        raise ValidationError('Telefone inválido. Use apenas números (pode conter +, -, (, ) e espaços).')


# ============================
# MODELOS PRINCIPAIS
# ============================

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True, error_messages={'unique': "Este e-mail já está cadastrado."})
    telefone = models.CharField(max_length=20, blank=True, validators=[validate_telefone])
    cpf = models.CharField(
        max_length=11,
        unique=True,
        blank=True, null=True,
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
        super().save(*args, **kwargs)
        # Processa a imagem para 1:1 (400x400) quando em storage local
        if self.imagem and hasattr(self.imagem, "path"):
            try:
                img_path = self.imagem.path
                with Image.open(img_path) as img:
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
                print(f"[SERVICO.save] Erro ao processar imagem: {e}")


class ServicoImagem(models.Model):
    # Mantém o related_name padrão (servicoimagem_set)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to="servicos/adicionais/")

    def __str__(self):
        return f"Imagem de {self.servico.nome}"


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


# ============================
# RESULTADOS (ALUNAS) — vitrine pública
# ============================

class ResultadoAluna(models.Model):
    nome_aluna = models.CharField(max_length=120)
    tecnica = models.CharField(max_length=120)
    foto = models.ImageField(upload_to="resultados/")
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0, db_index=True, help_text="Ordenação manual (menor primeiro)")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "-criado_em"]

    def __str__(self):
        return f"{self.nome_aluna} • {self.tecnica}"


# ============================
# PROVA SOCIAL (prints de feedback) — separado
# ============================

class ProvaSocial(models.Model):
    imagem = models.ImageField(upload_to="provas/")
    legenda = models.CharField(max_length=160, blank=True)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "-criado_em"]
        verbose_name = "Prova social"
        verbose_name_plural = "Provas sociais"

    def __str__(self):
        return self.legenda or f"ProvaSocial #{self.pk}"


# ============================
# EXTRAS
# ============================

class Notificacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notificacoes")
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"Notificação para {self.usuario.username}: {self.mensagem[:50]}..."


class Avaliacao(models.Model):
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name="avaliacoes")
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avaliacoes")
    nota = models.IntegerField()
    comentario = models.TextField(blank=True, null=True)
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("servico", "cliente")

    def __str__(self):
        return f"Avaliação de {self.servico.nome} por {self.cliente.username} - Nota {self.nota}"
