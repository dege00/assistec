import os
import secrets
import uuid
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone


def gerar_token():
    return secrets.token_urlsafe(8)


def _extensao_segura(filename, padrao=".jpg"):
    ext = os.path.splitext(filename or "")[1].lower()
    return ext if ext in {".jpg", ".jpeg", ".png", ".webp"} else padrao


def caminho_foto(instance, filename):
    """Nome aleatório: dificulta a enumeração de fotos de outras lojas."""
    return f"fotos/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{_extensao_segura(filename)}"


def caminho_assinatura(instance, filename):
    return f"assinaturas/{timezone.now():%Y/%m}/{uuid.uuid4().hex}.png"


def caminho_logo(instance, filename):
    return f"logos/{uuid.uuid4().hex}{_extensao_segura(filename)}"


class Loja(models.Model):
    """Cada assistência técnica = 1 loja (multiempresa / SaaS)."""
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    documento = models.CharField("CNPJ/CPF", max_length=20, blank=True)
    endereco = models.CharField(max_length=200, blank=True)
    termo_garantia = models.TextField(blank=True, default="Garantia de 90 dias sobre o serviço executado. Não cobre mau uso, queda ou contato com líquidos.")
    logo = models.ImageField(upload_to=caminho_logo, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    class Cargo(models.TextChoices):
        ADMIN = "admin", "Administrador"
        ATENDENTE = "atendente", "Atendente"
        TECNICO = "tecnico", "Técnico"

    loja = models.ForeignKey(Loja, null=True, blank=True, on_delete=models.CASCADE, related_name="usuarios")
    cargo = models.CharField(max_length=12, choices=Cargo.choices, default=Cargo.ADMIN)
    telefone = models.CharField(max_length=20, blank=True)

    @property
    def eh_admin(self):
        return self.cargo == self.Cargo.ADMIN or self.is_superuser


class PorLoja(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True


class Cliente(PorLoja):
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    documento = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Peca(PorLoja):
    nome = models.CharField(max_length=120)
    sku = models.CharField("Código / código de barras", max_length=60, blank=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    quantidade = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    minimo = models.IntegerField("Estoque mínimo", default=1, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class OrdemServico(PorLoja):
    class Status(models.TextChoices):
        ORCAMENTO = "orcamento", "Orçamento"
        EM_ANALISE = "em_analise", "Em análise"
        AGUARDANDO_PECA = "aguardando_peca", "Aguardando peça"
        EM_SERVICO = "em_servico", "Em serviço"
        FINALIZADO = "finalizado", "Finalizado"
        PAGO = "pago", "Pago"
        CANCELADO = "cancelado", "Cancelado"

    class Categoria(models.TextChoices):
        CELULAR = "celular", "Celular"
        OUTRO = "outro", "Outro"

    numero = models.PositiveIntegerField(editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="ordens")
    tecnico = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    categoria = models.CharField(max_length=10, choices=Categoria.choices, default=Categoria.OUTRO)
    tipo_aparelho = models.CharField(max_length=40, default="")
    marca = models.CharField(max_length=60, blank=True)
    modelo = models.CharField(max_length=60, blank=True)
    numero_serie = models.CharField("Nº de série", max_length=40, blank=True)
    imei = models.CharField("IMEI", max_length=40, blank=True)
    senha_aparelho = models.CharField(max_length=60, blank=True)
    acessorios = models.CharField(max_length=200, blank=True)
    defeito = models.TextField("Defeito relatado")
    laudo = models.TextField("Laudo técnico", blank=True)
    checklist = models.TextField("Estado do aparelho na entrada / checklist", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EM_ANALISE)
    token = models.CharField(max_length=16, default=gerar_token, unique=True, editable=False)
    assinatura = models.ImageField(upload_to=caminho_assinatura, blank=True, null=True)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    garantia_dias = models.PositiveIntegerField(default=90)
    previsao_entrega = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    entregue_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        unique_together = [("loja", "numero")]

    def save(self, *args, **kwargs):
        if not self.numero:
            with transaction.atomic():
                Loja.objects.select_for_update().get(pk=self.loja_id)  # serializa a numeração por loja
                ultimo = OrdemServico.objects.filter(loja=self.loja).aggregate(m=Max("numero"))["m"] or 0
                self.numero = ultimo + 1
                super().save(*args, **kwargs)
                HistoricoStatus.objects.create(os=self, status=self.status)
            return
        super().save(*args, **kwargs)

    def mudar_status(self, novo):
        if novo == self.status:
            return
        self.status = novo
        if novo == self.Status.PAGO and not self.entregue_em:
            self.entregue_em = timezone.now()
        self.save()
        HistoricoStatus.objects.create(os=self, status=novo)

    @property
    def subtotal(self):
        return sum((i.subtotal for i in self.itens.all()), Decimal("0"))

    @property
    def total(self):
        return max(self.subtotal - self.desconto, Decimal("0"))

    @property
    def custo(self):
        return sum((i.custo_unitario * i.quantidade for i in self.itens.all()), Decimal("0"))

    @property
    def lucro(self):
        return self.total - self.custo

    @property
    def pago(self):
        return sum((p.valor for p in self.lancamentos.all() if p.tipo == "entrada"), Decimal("0"))

    def __str__(self):
        return f"OS #{self.numero} - {self.cliente}"


class HistoricoStatus(models.Model):
    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name="historico")
    status = models.CharField(max_length=20, choices=OrdemServico.Status.choices)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em"]


class ItemOS(models.Model):
    class Tipo(models.TextChoices):
        PECA = "peca", "Peça"
        SERVICO = "servico", "Serviço"

    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name="itens")
    tipo = models.CharField(max_length=8, choices=Tipo.choices, default=Tipo.SERVICO)
    peca = models.ForeignKey(Peca, null=True, blank=True, on_delete=models.SET_NULL)
    descricao = models.CharField(max_length=160)
    quantidade = models.PositiveIntegerField(default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    @property
    def subtotal(self):
        return self.valor_unitario * self.quantidade


class FotoOS(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SERVICO = "servico", "Serviço"

    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name="fotos")
    imagem = models.ImageField(upload_to=caminho_foto)
    legenda = models.CharField(max_length=120, blank=True)
    visivel_cliente = models.BooleanField(default=False)
    tipo = models.CharField(max_length=8, choices=Tipo.choices, default=Tipo.ENTRADA)
    criado_em = models.DateTimeField(auto_now_add=True)


class Lancamento(PorLoja):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SAIDA = "saida", "Saída"

    tipo = models.CharField(max_length=8, choices=Tipo.choices)
    descricao = models.CharField(max_length=160)
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    forma = models.CharField(max_length=20, blank=True, default="dinheiro")
    os = models.ForeignKey(OrdemServico, null=True, blank=True, on_delete=models.SET_NULL, related_name="lancamentos")
    data = models.DateField(default=timezone.localdate)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
