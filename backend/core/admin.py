from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Cliente, FotoOS, HistoricoStatus, ItemOS, Lancamento, Loja, OrdemServico, Peca, Usuario

admin.site.register(Loja)
admin.site.register(Usuario, UserAdmin)
for m in (Cliente, Peca, OrdemServico, ItemOS, FotoOS, Lancamento, HistoricoStatus):
    admin.site.register(m)
