# agendamentos/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Cliente, Servico, Agendamento

# ===========================
# CLIENTE
# ===========================
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone', 'cpf']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
        }

# ===========================
# SERVIÇO
# ===========================
class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'descricao', 'duracao', 'preco', 'imagem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duracao': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'step': 5}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'imagem': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_imagem(self):
        """Valida proporção 1:1 (quadrado) com tolerância de ±6%."""
        imagem = self.cleaned_data.get('imagem')
        if not imagem:
            return imagem

        try:
            from PIL import Image
            from io import BytesIO

            data = imagem.read()
            img = Image.open(BytesIO(data))
            w, h = img.size
            img.close()

            # rebobina pro Django poder ler/salvar
            try:
                imagem.seek(0)
            except Exception:
                pass

            ratio = w / float(h) if h else 0.0
            if abs(ratio - 1.0) > 0.06:
                raise forms.ValidationError(
                    "A imagem deve ser QUADRADA (proporção 1:1). Ex.: 800×800, 1200×1200."
                )
        except Exception:
            try:
                imagem.seek(0)
            except Exception:
                pass

        return imagem

# ===========================
# AGENDAMENTO
# ===========================
class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['cliente', 'servico', 'data_hora', 'status']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'servico': forms.Select(attrs={'class': 'form-select'}),
            'data_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

# ===========================
# USER UPDATE (Auth)
# ===========================
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email']

# ===========================
# PROFILE UPDATE
# (caso você tenha um modelo Profile, se não tiver pode remover depois)
# ===========================
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Cliente  # 🔄 se você tiver um Profile separado, troque aqui
        fields = ['telefone', 'cpf']

# ===========================
# CONFIGURAÇÃO (dummy)
# ===========================
class ConfiguracaoForm(forms.Form):
    duracao_padrao = forms.IntegerField(
        label="Duração padrão do agendamento (minutos)",
        min_value=5,
        initial=60,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    intervalo = forms.IntegerField(
        label="Intervalo entre agendamentos (minutos)",
        min_value=5,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
