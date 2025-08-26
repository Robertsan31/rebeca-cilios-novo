from django import forms
from .models import Cliente, Servico

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone', 'cpf']
        widgets = {
            # NÃO usar required=True aqui; o JS da página controla conforme a seleção
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
        }

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
        """
        Valida apenas a PROPORÇÃO 1:1 (quadrado) com tolerância de ±6%.
        """
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
            # se algo falhar na validação, apenas rebobina e deixa passar
            try:
                imagem.seek(0)
            except Exception:
                pass

        return imagem
