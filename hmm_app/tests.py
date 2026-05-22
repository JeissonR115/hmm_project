"""
Tests para la app HMM.
Cubre: lógica pura, modelos, vistas y formularios.
"""

from django.test import TestCase, Client
from django.urls import reverse
import json

from hmm_app.hmm_logic import forward, viterbi, backward, baum_welch, parse_obs_string
from hmm_app.models import Experimento


# ── Tests de lógica pura ─────────────────────────────────────────────

class HMMLgicoTest(TestCase):

    def setUp(self):
        self.pi = [0.6, 0.4]
        self.A  = [[0.7, 0.3], [0.4, 0.6]]
        self.B  = [[0.5, 0.4, 0.1], [0.1, 0.3, 0.6]]
        self.obs = [0, 1, 2]

    def test_forward_devuelve_prob_positiva(self):
        _, prob = forward(self.obs, self.pi, self.A, self.B)
        self.assertGreater(prob, 0)
        self.assertLessEqual(prob, 1)

    def test_forward_secuencia_un_elemento(self):
        _, prob = forward([0], self.pi, self.A, self.B)
        esperado = self.pi[0]*self.B[0][0] + self.pi[1]*self.B[1][0]
        self.assertAlmostEqual(prob, esperado, places=8)

    def test_viterbi_longitud_correcta(self):
        estados = viterbi(self.obs, self.pi, self.A, self.B)
        self.assertEqual(len(estados), len(self.obs))

    def test_viterbi_estados_validos(self):
        estados = viterbi(self.obs, self.pi, self.A, self.B)
        for s in estados:
            self.assertIn(s, [0, 1])

    def test_backward_ultimo_es_uno(self):
        beta = backward(self.obs, self.A, self.B)
        self.assertEqual(beta[-1][0], 1.0)
        self.assertEqual(beta[-1][1], 1.0)

    def test_baum_welch_no_disminuye_prob(self):
        _, prob_antes = forward(self.obs, self.pi, self.A, self.B)
        pi2, A2, B2 = baum_welch(self.obs, self.pi, self.A, self.B, n_iter=5)
        _, prob_despues = forward(self.obs, pi2, A2, B2)
        self.assertGreaterEqual(prob_despues, prob_antes - 1e-8)

    def test_parse_obs_string_ok(self):
        self.assertEqual(parse_obs_string('0,1,2,0'), [0, 1, 2, 0])

    def test_parse_obs_string_error_valor(self):
        with self.assertRaises(ValueError):
            parse_obs_string('0,3,1')

    def test_parse_obs_string_error_vacio(self):
        with self.assertRaises(ValueError):
            parse_obs_string('')


# ── Tests del modelo Django ──────────────────────────────────────────

class ExperimentoModelTest(TestCase):

    def setUp(self):
        self.exp = Experimento.objects.create(
            nombre='Test exp',
            estado_0='Lluvia',
            estado_1='Sol',
            pi_json='[0.5, 0.5]',
            A_json='[[0.7,0.3],[0.4,0.6]]',
            B_json='[[0.6,0.3,0.1],[0.1,0.4,0.5]]',
            observaciones_json='[0,1,2]',
            probabilidad_forward=0.05,
            estados_viterbi_json='[0,0,1]',
        )

    def test_str(self):
        self.assertIn('Test exp', str(self.exp))

    def test_get_pi(self):
        self.assertEqual(self.exp.get_pi(), [0.5, 0.5])

    def test_get_viterbi_names(self):
        names = self.exp.get_viterbi_names()
        self.assertEqual(names, ['Lluvia', 'Lluvia', 'Sol'])

    def test_get_obs_names(self):
        self.assertEqual(self.exp.get_obs_names(), ['Caminar', 'Compras', 'Limpiar'])


# ── Tests de vistas ──────────────────────────────────────────────────

class VistasTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.exp = Experimento.objects.create(
            nombre='Experimento vista',
            pi_json='[0.5,0.5]',
            A_json='[[0.7,0.3],[0.4,0.6]]',
            B_json='[[0.6,0.3,0.1],[0.1,0.4,0.5]]',
            observaciones_json='[0,1,2]',
            probabilidad_forward=0.04,
            estados_viterbi_json='[0,0,1]',
        )

    def test_lista_status_200(self):
        r = self.client.get(reverse('lista'))
        self.assertEqual(r.status_code, 200)

    def test_lista_contiene_experimento(self):
        r = self.client.get(reverse('lista'))
        self.assertContains(r, 'Experimento vista')

    def test_detalle_status_200(self):
        r = self.client.get(reverse('detalle', args=[self.exp.pk]))
        self.assertEqual(r.status_code, 200)

    def test_detalle_404_inexistente(self):
        r = self.client.get(reverse('detalle', args=[9999]))
        self.assertEqual(r.status_code, 404)

    def test_crear_get_status_200(self):
        r = self.client.get(reverse('crear'))
        self.assertEqual(r.status_code, 200)

    def test_crear_post_valido(self):
        data = {
            'nombre': 'Nuevo exp',
            'descripcion': '',
            'estado_0': 'Lluvia',
            'estado_1': 'Sol',
            'pi_0': '0.5', 'pi_1': '0.5',
            'a00': '0.7', 'a01': '0.3',
            'a10': '0.4', 'a11': '0.6',
            'b00': '0.6', 'b01': '0.3', 'b02': '0.1',
            'b10': '0.1', 'b11': '0.4', 'b12': '0.5',
            'observaciones_str': '0,1,2',
        }
        r = self.client.post(reverse('crear'), data)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Experimento.objects.filter(nombre='Nuevo exp').exists())

    def test_eliminar_post(self):
        r = self.client.post(reverse('eliminar', args=[self.exp.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Experimento.objects.filter(pk=self.exp.pk).exists())

    def test_simulador_get(self):
        r = self.client.get(reverse('simulador'))
        self.assertEqual(r.status_code, 200)

    def test_simulador_post(self):
        data = {
            's0':'Lluvia','s1':'Sol','obs_str':'0,1,2',
            'pi0':'0.5','pi1':'0.5',
            'a00':'0.7','a01':'0.3','a10':'0.4','a11':'0.6',
            'b00':'0.6','b01':'0.3','b02':'0.1',
            'b10':'0.1','b11':'0.4','b12':'0.5',
        }
        r = self.client.post(reverse('simulador'), data)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Forward')
