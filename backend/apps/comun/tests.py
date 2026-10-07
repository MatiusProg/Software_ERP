from django.test import TestCase


class SaludTest(TestCase):
    def test_responde_ok_sin_login(self):
        r = self.client.get("/salud/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"estado": "ok"})

    def test_raiz_no_da_404(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["salud"], "/salud/")
