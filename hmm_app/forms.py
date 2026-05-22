from django import forms
from .models import Experimento
from .hmm_logic import parse_obs_string
import json


class ExperimentoForm(forms.ModelForm):
    """
    Formulario para crear/editar un experimento.
    Los campos de matrices se manejan como campos individuales de texto
    para facilitar la edición en el template.
    """

    # Campos planos para π
    pi_0 = forms.FloatField(min_value=0, max_value=1, label='π estado 0', initial=0.5,
                             widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    pi_1 = forms.FloatField(min_value=0, max_value=1, label='π estado 1', initial=0.5,
                             widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))

    # Campos planos para A
    a00 = forms.FloatField(min_value=0, max_value=1, label='A[0→0]', initial=0.7,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    a01 = forms.FloatField(min_value=0, max_value=1, label='A[0→1]', initial=0.3,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    a10 = forms.FloatField(min_value=0, max_value=1, label='A[1→0]', initial=0.4,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    a11 = forms.FloatField(min_value=0, max_value=1, label='A[1→1]', initial=0.6,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))

    # Campos planos para B
    b00 = forms.FloatField(min_value=0, max_value=1, label='B[0,Caminar]', initial=0.6,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    b01 = forms.FloatField(min_value=0, max_value=1, label='B[0,Compras]', initial=0.3,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    b02 = forms.FloatField(min_value=0, max_value=1, label='B[0,Limpiar]', initial=0.1,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    b10 = forms.FloatField(min_value=0, max_value=1, label='B[1,Caminar]', initial=0.1,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    b11 = forms.FloatField(min_value=0, max_value=1, label='B[1,Compras]', initial=0.4,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))
    b12 = forms.FloatField(min_value=0, max_value=1, label='B[1,Limpiar]', initial=0.5,
                            widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'field'}))

    # Secuencia
    observaciones_str = forms.CharField(
        label='Secuencia de observaciones',
        initial='0,1,2,1,0',
        help_text='Separa con comas. 0=Caminar, 1=Compras, 2=Limpiar',
        widget=forms.TextInput(attrs={'placeholder': '0,1,2,0,1', 'class': 'field'})
    )

    class Meta:
        model = Experimento
        fields = ['nombre', 'descripcion', 'estado_0', 'estado_1']
        widgets = {
            'nombre':      forms.TextInput(attrs={'class': 'field'}),
            'descripcion': forms.Textarea(attrs={'rows': 2, 'class': 'field'}),
            'estado_0':    forms.TextInput(attrs={'class': 'field'}),
            'estado_1':    forms.TextInput(attrs={'class': 'field'}),
        }

    def clean(self):
        cd = super().clean()

        # Validar que π sume ~1
        pi0 = cd.get('pi_0', 0)
        pi1 = cd.get('pi_1', 0)
        if abs(pi0 + pi1 - 1.0) > 0.05:
            self.add_error('pi_0', 'π debe sumar 1.0')

        # Validar filas de A
        if abs(cd.get('a00', 0) + cd.get('a01', 0) - 1.0) > 0.05:
            self.add_error('a00', 'Fila 0 de A debe sumar 1.0')
        if abs(cd.get('a10', 0) + cd.get('a11', 0) - 1.0) > 0.05:
            self.add_error('a10', 'Fila 1 de A debe sumar 1.0')

        # Validar filas de B
        if abs(cd.get('b00', 0) + cd.get('b01', 0) + cd.get('b02', 0) - 1.0) > 0.05:
            self.add_error('b00', 'Fila 0 de B debe sumar 1.0')
        if abs(cd.get('b10', 0) + cd.get('b11', 0) + cd.get('b12', 0) - 1.0) > 0.05:
            self.add_error('b10', 'Fila 1 de B debe sumar 1.0')

        # Validar observaciones
        obs_str = cd.get('observaciones_str', '')
        try:
            parse_obs_string(obs_str)
        except ValueError as e:
            self.add_error('observaciones_str', str(e))

        return cd

    def save(self, commit=True):
        instance = super().save(commit=False)
        cd = self.cleaned_data

        instance.pi_json = json.dumps([cd['pi_0'], cd['pi_1']])
        instance.A_json  = json.dumps([[cd['a00'], cd['a01']], [cd['a10'], cd['a11']]])
        instance.B_json  = json.dumps([[cd['b00'], cd['b01'], cd['b02']],
                                        [cd['b10'], cd['b11'], cd['b12']]])
        obs = parse_obs_string(cd['observaciones_str'])
        instance.observaciones_json = json.dumps(obs)

        if commit:
            instance.save()
        return instance
