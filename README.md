# hogar-de-los-alpes-servicio-dddesacoplados

## Instalacion

1. Crear y activar un entorno virtual.
2. Instalar el proyecto en modo editable:

```bash
pip install -e .
```

## Ejecutar pruebas

```bash
python -m pytest -q
```

## Persistencia PostgreSQL (Bloque 2.4)

El puerto `RepositorioSolicitudesPartner` tiene dos implementaciones:
- `RepositorioSolicitudesPartnerMemoria` (usada por `crear_servicio_solicitudes_partner()`, sin dependencias externas, para tests unitarios).
- `RepositorioSolicitudesPartnerPostgres` (adaptador real, usado explicitamente via `crear_servicio_solicitudes_partner_postgres(conexion)`).

### Variables de entorno

```
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

Ver ejemplo en `.env.example`.

### Levantar PostgreSQL localmente

```bash
docker compose up -d
```

Esto expone PostgreSQL en el puerto configurado (por defecto 5432) y crea la tabla `solicitudes_partner` a partir de `db/schema.sql`.

### Instalar dependencias para PostgreSQL

```bash
pip install -e ".[postgres]"
```

### Ejecutar pruebas de integracion

Con PostgreSQL levantado (`docker compose up -d`) y las variables de entorno exportadas:

```bash
python -m pytest tests/integration -q
```

Si `psycopg` no esta instalado o PostgreSQL no esta disponible, estas pruebas se omiten (skip) de forma explicita y no afectan la suite unitaria.

