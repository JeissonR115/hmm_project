from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.ExperimentoListView.as_view(), name='lista'),
    path('nuevo/',                        views.crear_experimento,              name='crear'),
    path('<int:pk>/',                     views.ExperimentoDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/',              views.editar_experimento,             name='editar'),
    path('<int:pk>/eliminar/',            views.ExperimentoDeleteView.as_view(), name='eliminar'),
    path('simulador/',                    views.simulador,                      name='simulador'),
]
