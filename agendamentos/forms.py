# agendamentos/forms.py
from django import forms
from .models import Cliente, Servico

# O ClienteForm permanece igual, não precisa mexer aqui.
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone', 'cpf']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
        }

# O ServicoForm foi corrigido abaixo.
class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        # CORREÇÃO: Removemos 'duracao' e adicionamos 'imagem'
        fields = ['nome', 'descricao', 'preco', 'imagem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preco': forms.NumberInput(attrs={'class': 'form-control'}),
            # Adicionamos o widget para o novo campo de imagem
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
        }