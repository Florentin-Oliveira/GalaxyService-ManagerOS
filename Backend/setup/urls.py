from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from Aplicacao.views import (FavoritasClienteViewSet, FavoritasOrdemViewSet, UserViewSet, ClienteViewSet, OrdemViewSet, SignupView, LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView, PasswordChangeView, CompartilhamentoViewSet, ComentarioViewSet, AnexoViewSet, RelatorioPDFView, NotificacaoView)

schema_view = get_schema_view(
    openapi.Info(
        title="API de Gerenciamento de Ordem de Serviço",
        default_version='v1',
        description="Gerenciamento de Ordem de Serviço",
        terms_of_service="#",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename="tecnico")
router.register('clientes', ClienteViewSet, basename="cliente")
router.register('ordens', OrdemViewSet, basename="ordemdeservico")
router.register('favoritas/clientes', FavoritasClienteViewSet, basename='favoritas-clientes')
router.register('favoritas/ordens', FavoritasOrdemViewSet, basename='favoritas-ordens')
router.register('compartilhamento', CompartilhamentoViewSet, basename="compartilhamento")
router.register('comentario', ComentarioViewSet, basename="comentario")
router.register('anexo', AnexoViewSet, basename="anexo")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/sign-up/', SignupView.as_view(), name='sign-up'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('api/password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/password-change/', PasswordChangeView.as_view(), name='password_change'),
    path('api/relatorio-pdf/<int:ordem_id>/', RelatorioPDFView.as_view(), name='relatorio_pdf'),
    path('api/notificacoes/', NotificacaoView.as_view(), name='notificacoes'),
    path('api/notificacoes/Limpar/', NotificacaoView.as_view(), name='notificacoes-limpar'),
    path('api/compartilhamento/ordem/<int:pk>/permissao/', CompartilhamentoViewSet.as_view({'get': 'permissao'}), name='compartilhamento-permissao'),
    path('api/notificacoes/<int:id>/Lido/', NotificacaoView.as_view(), name='notificacoes-lido'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)