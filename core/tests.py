from django.contrib.auth.models import Group, User
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Registro

CLAVE = "clave-de-prueba-123"


class ApiRegistrosTests(APITestCase):
    def setUp(self):
        for rol in ("admin", "normal", "viewer"):
            user = User.objects.create_user(username=rol, password=CLAVE)
            grupo, _ = Group.objects.get_or_create(name=rol)
            user.groups.add(grupo)
        self.registro = Registro.objects.create(
            nombre="Ana", patente="ABCD12", inasistencias=0, resultado="Aceptado"
        )

    def entrar(self, username):
        r = self.client.post(
            "/api/token/", {"username": username, "password": CLAVE}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        return r.data

    def test_sin_token_401(self):
        r = self.client.get("/api/registros/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_clave_mala_401(self):
        r = self.client.post(
            "/api/token/", {"username": "admin", "password": "mala"}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(r.data["detail"], "Usuario o contrasena incorrectos.")

    def test_token_falso_401_en_espanol(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token.falso.x")
        r = self.client.get("/api/registros/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(r.data["detail"].startswith("El token no es valido"))

    def test_filtros(self):
        Registro.objects.create(
            nombre="Luis Perez", patente="BB1234", inasistencias=3,
            resultado="Rechazado: el cliente acumula demasiados no-show",
        )
        self.entrar("viewer")
        r = self.client.get("/api/registros/", {"resultado": "Aceptado"})
        self.assertEqual([x["nombre"] for x in r.data["results"]], ["Ana"])
        r = self.client.get("/api/registros/", {"patente": "bb-1234"})
        self.assertEqual([x["nombre"] for x in r.data["results"]], ["Luis Perez"])
        r = self.client.get("/api/registros/", {"nombre": "lui"})
        self.assertEqual(r.data["count"], 1)

    def test_listar_200_paginado(self):
        self.entrar("viewer")
        r = self.client.get("/api/registros/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 1)
        self.assertNotIn("eliminado", r.data["results"][0])

    def test_crear_201_y_resultado_lo_decide_la_regla(self):
        self.entrar("normal")
        r = self.client.post(
            "/api/registros/",
            {"nombre": "Luis", "inasistencias": 3, "resultado": "Aceptado"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            r.data["resultado"], "Rechazado: el cliente acumula demasiados no-show"
        )

    def test_crear_invalido_400(self):
        self.entrar("normal")
        r = self.client.post(
            "/api/registros/",
            {"nombre": "Luis", "inasistencias": -1, "patente": "XX"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inasistencias", r.data)
        self.assertIn("patente", r.data)

    def test_viewer_no_crea_403(self):
        self.entrar("viewer")
        r = self.client.post(
            "/api/registros/", {"nombre": "Luis", "inasistencias": 0}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_no_borra_403(self):
        self.entrar("normal")
        r = self.client.delete(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_patch_200(self):
        self.entrar("admin")
        r = self.client.patch(
            f"/api/registros/{self.registro.pk}/", {"inasistencias": 5}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data["resultado"].startswith("Rechazado"))

    def test_admin_borra_204_y_es_borrado_logico(self):
        self.entrar("admin")
        r = self.client.delete(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.registro.refresh_from_db()
        self.assertTrue(self.registro.eliminado)
        r = self.client.get(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_id_inexistente_404(self):
        self.entrar("viewer")
        r = self.client.get("/api/registros/9999/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(r.data["detail"], "No existe un registro con ese id.")

    def test_aceptados_200(self):
        self.entrar("viewer")
        r = self.client.get("/api/registros/aceptados/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 1)

    def test_refresh_entrega_nuevo_access(self):
        tokens = self.entrar("viewer")
        self.client.credentials()
        r = self.client.post(
            "/api/token/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)

    def test_pantallas_html_siguen_vivas(self):
        r = self.client.get("/login/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
