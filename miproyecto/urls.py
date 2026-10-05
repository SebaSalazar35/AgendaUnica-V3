from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core import views
from core.api_views import RegistroViewSet

router = DefaultRouter()
router.register(r"registros", RegistroViewSet, basename="registro")

urlpatterns = [
    path("admin/", admin.site.urls),
    # API REST (ES3)
    path("api/token/", TokenObtainPairView.as_view(), name="api_token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/", include(router.urls)),
    # Pantallas HTML (ES2)
    path("", views.inicio, name="inicio"),
    path("login/", views.vista_login, name="login"),
    path("logout/", views.vista_logout, name="logout"),
    path("registro/", views.registro_cuenta, name="registro"),
    path("calendario/", views.calendario, name="calendario"),
    path("reservar/", views.reservar, name="reservar"),
    path("mis-horas/<int:pk>/liberar/", views.cancelar_propia, name="cancelar_propia"),
    path("mis-horas/", views.mis_horas, name="mis_horas"),
    path("registros/", views.lista, name="lista"),
    path("registros/crear/", views.crear, name="crear"),
    path("registros/<int:pk>/editar/", views.editar, name="editar"),
    path("registros/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("panel/", views.panel, name="panel"),
    path("panel/horarios/", views.horarios, name="horarios"),
    path("panel/reservas/<int:pk>/liberar/", views.liberar, name="liberar"),
    path("panel/bloquear/", views.bloquear_hora, name="bloquear_hora"),
    path("panel/bloqueos/<int:pk>/quitar/", views.desbloquear_hora, name="desbloquear_hora"),
    path("resumen/", views.resumen, name="resumen"),
]
