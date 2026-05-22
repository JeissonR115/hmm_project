# HMM App — Django

Aplicación web para simular y guardar experimentos con el **Modelo Oculto de Markov**.

## Requisitos

- Python 3.10+
- pip

## Instalación

```bash
# 1. Instalar dependencias
pip install Django

# 2. Entrar a la carpeta del proyecto
cd hmm_project

# 3. Migrar base de datos
python manage.py migrate

# 4. Crear superusuario (para el panel admin)
python manage.py createsuperuser

# 5. Correr el servidor
python manage.py runserver
```

Abre http://127.0.0.1:8000

## Tests

```bash
python manage.py test hmm_app
```

## Estructura

```
hmm_project/
├── hmm_project/          # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── hmm_app/              # App principal
│   ├── hmm_logic.py      # Lógica HMM pura (sin Django)
│   ├── models.py         # Modelo Experimento → SQLite
│   ├── views.py          # Vistas normales + genéricas
│   ├── forms.py          # Formulario con validación
│   ├── urls.py           # UrlConf de la app
│   ├── admin.py          # Panel admin
│   ├── tests.py          # Tests
│   └── templates/
│       └── hmm_app/
│           ├── base.html
│           ├── lista.html
│           ├── detalle.html
│           ├── form.html
│           ├── simulador.html
│           └── confirmar_eliminar.html
└── manage.py
```

## URLs

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/` | ListView | Lista de experimentos |
| `/nuevo/` | función | Crear experimento |
| `/<pk>/` | DetailView | Ver resultado |
| `/<pk>/editar/` | función | Editar |
| `/<pk>/eliminar/` | DeleteView | Eliminar |
| `/simulador/` | función | Simulador rápido + Baum-Welch |
| `/admin/` | Django admin | Panel completo |

## Cobertura de requisitos

| Requisito | Dónde |
|-----------|-------|
| Vistas | `views.py` — `crear_experimento`, `editar_experimento`, `simulador` |
| Modelos | `models.py` — `Experimento` |
| UrlConf | `urls.py` |
| Vistas genéricas | `ListView`, `DetailView`, `DeleteView` en `views.py` |
| Formularios | `forms.py` — `ExperimentoForm` |
| CRUD SQLite | Crear/leer/editar/eliminar experimentos |
| Panel Admin | `admin.py` — `ExperimentoAdmin` |
| Testing | `tests.py` — 15 tests |
