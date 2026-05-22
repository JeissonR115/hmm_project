from django.contrib import admin
from .models import Experimento


@admin.register(Experimento)
class ExperimentoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'estado_0', 'estado_1', 'probabilidad_forward', 'creado_en')
    list_filter   = ('creado_en',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('probabilidad_forward', 'estados_viterbi_json', 'creado_en')
    fieldsets = (
        ('General', {'fields': ('nombre', 'descripcion')}),
        ('Estados', {'fields': ('estado_0', 'estado_1')}),
        ('Parámetros', {'fields': ('pi_json', 'A_json', 'B_json')}),
        ('Datos', {'fields': ('observaciones_json',)}),
        ('Resultados (auto)', {'fields': ('probabilidad_forward', 'estados_viterbi_json', 'creado_en')}),
    )
