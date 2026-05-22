import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Experimento
from .forms import ExperimentoForm
from .hmm_logic import forward, viterbi, baum_welch, parse_obs_string


# ── Vista genérica: lista de experimentos ────────────────────────────

class ExperimentoListView(ListView):
    model = Experimento
    template_name = 'hmm_app/lista.html'
    context_object_name = 'experimentos'
    paginate_by = 10


# ── Vista genérica: detalle de un experimento ────────────────────────

class ExperimentoDetailView(DetailView):
    model = Experimento
    template_name = 'hmm_app/detalle.html'
    context_object_name = 'exp'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        exp = self.object
        obs = exp.get_obs()
        pi  = exp.get_pi()
        A   = exp.get_A()
        B   = exp.get_B()

        _, prob   = forward(obs, pi, A, B)
        estados   = viterbi(obs, pi, A, B)
        obs_names = exp.get_obs_names()
        st_names  = [exp.get_state_name(s) for s in estados]

        ctx['prob']     = prob
        ctx['pares']    = list(zip(obs_names, st_names))
        ctx['A']        = A
        ctx['B']        = B
        ctx['pi']       = pi
        return ctx


# ── Vista genérica: eliminar ─────────────────────────────────────────

class ExperimentoDeleteView(DeleteView):
    model = Experimento
    template_name = 'hmm_app/confirmar_eliminar.html'
    success_url = reverse_lazy('lista')
    context_object_name = 'exp'


# ── Vista normal: crear experimento ─────────────────────────────────

def crear_experimento(request):
    if request.method == 'POST':
        form = ExperimentoForm(request.POST)
        if form.is_valid():
            exp = form.save()
            # Calcular y guardar resultados
            obs = exp.get_obs()
            _, prob = forward(obs, exp.get_pi(), exp.get_A(), exp.get_B())
            estados = viterbi(obs, exp.get_pi(), exp.get_A(), exp.get_B())
            exp.probabilidad_forward = prob
            exp.estados_viterbi_json = json.dumps(estados)
            exp.save()
            messages.success(request, f'Experimento "{exp.nombre}" creado.')
            return redirect('detalle', pk=exp.pk)
    else:
        form = ExperimentoForm()
    return render(request, 'hmm_app/form.html', {'form': form, 'accion': 'Crear'})


# ── Vista normal: editar experimento ────────────────────────────────

def editar_experimento(request, pk):
    exp = get_object_or_404(Experimento, pk=pk)
    if request.method == 'POST':
        form = ExperimentoForm(request.POST, instance=exp)
        if form.is_valid():
            exp = form.save()
            obs = exp.get_obs()
            _, prob = forward(obs, exp.get_pi(), exp.get_A(), exp.get_B())
            estados = viterbi(obs, exp.get_pi(), exp.get_A(), exp.get_B())
            exp.probabilidad_forward = prob
            exp.estados_viterbi_json = json.dumps(estados)
            exp.save()
            messages.success(request, 'Experimento actualizado.')
            return redirect('detalle', pk=exp.pk)
    else:
        pi = exp.get_pi(); A = exp.get_A(); B = exp.get_B()
        obs = exp.get_obs()
        initial = {
            'pi_0': pi[0], 'pi_1': pi[1],
            'a00': A[0][0], 'a01': A[0][1],
            'a10': A[1][0], 'a11': A[1][1],
            'b00': B[0][0], 'b01': B[0][1], 'b02': B[0][2],
            'b10': B[1][0], 'b11': B[1][1], 'b12': B[1][2],
            'observaciones_str': ','.join(str(o) for o in obs),
        }
        form = ExperimentoForm(instance=exp, initial=initial)
    return render(request, 'hmm_app/form.html', {'form': form, 'accion': 'Editar', 'exp': exp})


# ── Vista: simulador rápido (sin guardar) ────────────────────────────

def simulador(request):
    resultado = None
    form_data = {}

    if request.method == 'POST':
        obs_str = request.POST.get('obs_str', '0,1,2')
        s0 = request.POST.get('s0', 'Lluvia')
        s1 = request.POST.get('s1', 'Sol')
        entrenar = request.POST.get('entrenar') == '1'

        form_data = request.POST.dict()

        try:
            obs = parse_obs_string(obs_str)
            pi  = [float(request.POST.get('pi0', 0.5)), float(request.POST.get('pi1', 0.5))]
            A   = [[float(request.POST.get('a00', 0.7)), float(request.POST.get('a01', 0.3))],
                   [float(request.POST.get('a10', 0.4)), float(request.POST.get('a11', 0.6))]]
            B   = [[float(request.POST.get('b00', 0.6)), float(request.POST.get('b01', 0.3)), float(request.POST.get('b02', 0.1))],
                   [float(request.POST.get('b10', 0.1)), float(request.POST.get('b11', 0.4)), float(request.POST.get('b12', 0.5))]]

            if entrenar:
                pi, A, B = baum_welch(obs, pi, A, B, n_iter=15)
                form_data['pi0'] = f'{pi[0]:.4f}'
                form_data['pi1'] = f'{pi[1]:.4f}'

            _, prob  = forward(obs, pi, A, B)
            estados  = viterbi(obs, pi, A, B)
            obs_names = ['Caminar', 'Compras', 'Limpiar']
            st_names  = [s0 if s == 0 else s1 for s in estados]

            resultado = {
                'prob':   prob,
                'pares':  list(zip([obs_names[o] for o in obs], st_names, estados)),
                'pi':     pi,
                'A':      A,
                'B':      B,
                'entrenado': entrenar,
            }
        except (ValueError, ZeroDivisionError) as e:
            messages.error(request, str(e))

    return render(request, 'hmm_app/simulador.html', {
        'resultado': resultado,
        'form_data': form_data,
    })
