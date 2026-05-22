from django.db import models
import json


class Experimento(models.Model):
    """Guarda un experimento HMM completo con sus parámetros y resultados."""

    nombre       = models.CharField(max_length=120)
    descripcion  = models.TextField(blank=True)
    creado_en    = models.DateTimeField(auto_now_add=True)

    # Parámetros del modelo (guardados como JSON)
    estado_0     = models.CharField(max_length=50, default='Lluvia')
    estado_1     = models.CharField(max_length=50, default='Sol')
    pi_json      = models.TextField(default='[0.5, 0.5]')
    A_json       = models.TextField(default='[[0.7, 0.3], [0.4, 0.6]]')
    B_json       = models.TextField(default='[[0.6, 0.3, 0.1], [0.1, 0.4, 0.5]]')

    # Secuencia de observaciones
    observaciones_json = models.TextField(default='[0, 1, 2]')

    # Resultados calculados
    probabilidad_forward = models.FloatField(null=True, blank=True)
    estados_viterbi_json = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Experimento'
        verbose_name_plural = 'Experimentos'

    def __str__(self):
        return f"{self.nombre} ({self.creado_en:%Y-%m-%d %H:%M})"

    # Helpers para deserializar
    def get_pi(self):   return json.loads(self.pi_json)
    def get_A(self):    return json.loads(self.A_json)
    def get_B(self):    return json.loads(self.B_json)
    def get_obs(self):  return json.loads(self.observaciones_json)
    def get_viterbi(self):
        if self.estados_viterbi_json:
            return json.loads(self.estados_viterbi_json)
        return []

    def get_state_name(self, idx):
        return self.estado_0 if idx == 0 else self.estado_1

    def get_viterbi_names(self):
        return [self.get_state_name(s) for s in self.get_viterbi()]

    OBS_NAMES = ['Caminar', 'Compras', 'Limpiar']

    def get_obs_names(self):
        return [self.OBS_NAMES[o] for o in self.get_obs()]
