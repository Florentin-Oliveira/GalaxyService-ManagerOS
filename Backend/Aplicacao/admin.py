from django.contrib import admin
from .models import (Ordem, Cliente, FavoritasCliente, FavoritasOrdem, Anexo, Comentario, Compartilhamento)


# admin.py é usado para registrar modelos para que possam ser gerenciados através da interface administrativa do Django

admin.site.register(Ordem)
admin.site.register(Cliente)
admin.site.register(FavoritasCliente)
admin.site.register(FavoritasOrdem)
admin.site.register(Compartilhamento)
admin.site.register(Comentario)
admin.site.register(Anexo)