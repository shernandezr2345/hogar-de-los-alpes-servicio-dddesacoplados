"""Construccion de la conexion a PostgreSQL a partir de variables de entorno."""

from __future__ import annotations

import os

import psycopg


def obtener_configuracion_conexion() -> dict[str, str]:
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("DB_NAME", "hogar_alpes"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", "postgres"),
    }


def crear_conexion() -> psycopg.Connection:
    configuracion = obtener_configuracion_conexion()
    return psycopg.connect(autocommit=True, **configuracion)
