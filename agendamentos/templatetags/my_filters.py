from django import template

register = template.Library()

@register.filter
def make_range(value):
    """Cria um range para iteração em for."""
    try:
        return range(int(value))
    except:
        return []

@register.filter
def index(sequence, position):
    """Pega o item no índice da lista."""
    try:
        return sequence[position]
    except:
        return ''
