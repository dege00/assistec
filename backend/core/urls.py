from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("clientes", views.ClienteViewSet)
router.register("pecas", views.PecaViewSet)
router.register("os", views.OSViewSet)
router.register("itens", views.ItemOSViewSet, basename="itemos")
router.register("fotos", views.FotoViewSet, basename="fotoos")
router.register("lancamentos", views.LancamentoViewSet)
router.register("usuarios", views.UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("auth/login/", views.Login.as_view()),
    path("auth/refresh/", views.Refresh.as_view()),
    path("auth/trocar-senha/", views.TrocarSenha.as_view()),
    path("auth/eu/", views.Eu.as_view()),
    path("exportar/clientes/", views.ExportarClientes.as_view()),
    path("exportar/pecas/", views.ExportarPecas.as_view()),
    path("dashboard/", views.dashboard),
    path("publico/os/<str:token>/", views.acompanhar),
    path("", include(router.urls)),
]
