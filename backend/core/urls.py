from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
    path("auth/login/", TokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/registrar/", views.registrar),
    path("auth/eu/", views.Eu.as_view()),
    path("dashboard/", views.dashboard),
    path("publico/os/<str:token>/", views.acompanhar),
    path("", include(router.urls)),
]
