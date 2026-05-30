# Simulacion de atencion bancaria

Este proyecto implementa una simulacion de eventos discretos para analizar la atencion de clientes en un banco con 3 cajeros durante una jornada de 8 horas.

El programa evalua tiempos de servicio, tiempos de espera, tipos de usuarios, replicas de simulacion y diferentes configuraciones de asignacion de cajeros para retiros y pagos.

## Objetivo

Analizar el comportamiento operativo de un banco bajo distintas condiciones de atencion, con el fin de responder los siguientes puntos:

- Identificar el cajero con menor y mayor tiempo promedio de atencion.
- Calcular el promedio de usuarios por tipo y tipo de transaccion.
- Determinar el total de usuarios por replica y detectar las replicas con menor cantidad de usuarios.
- Evaluar si es necesario crear un nuevo cajero segun tiempos de espera y utilizacion.
- Comparar configuraciones de cajeros para proponer la mejor alternativa.

## Archivo principal

El proyecto contiene un unico script principal:

```text
Actividad4Bancos.py
```

Este archivo contiene:

- La clase `SimulacionBanco`, encargada de ejecutar la simulacion.
- La generacion de clientes, tipos de usuario y tipos de transaccion.
- El calculo de indicadores para los puntos del analisis.
- La comparacion de configuraciones de cajeros.
- La exportacion de resultados a Excel.
- La generacion de graficas para el informe.

## Requisitos

Se requiere tener instalado Python 3.10 o superior.

Tambien se deben instalar las siguientes librerias:

```bash
pip install numpy pandas matplotlib openpyxl
```

`openpyxl` es necesario para que `pandas` pueda guardar los resultados en archivos `.xlsx`.

## Como ejecutar el proyecto

Desde la carpeta del proyecto, ejecutar:

```bash
python Actividad4Bancos.py
```

Al ejecutarse, el programa:

1. Crea la carpeta `resultados_simulacion`.
2. Ejecuta 10 replicas de la simulacion.
3. Imprime en consola los resultados de cada punto.
4. Guarda tablas de resultados en archivos Excel.
5. Genera y muestra graficas con `matplotlib`.

## Parametros principales

La simulacion se configura desde la clase `SimulacionBanco`:

```python
sim = SimulacionBanco(num_cajeros=3, horas_operacion=8)
```

Parametros disponibles:

- `num_cajeros`: numero de cajeros disponibles.
- `horas_operacion`: duracion de la jornada en horas.
- `configuracion`: distribucion de cajeros por tipo de transaccion.

Configuraciones soportadas:

- `mixto`: todos los cajeros atienden retiros y pagos.
- `1r2p`: 1 cajero para retiros y 2 cajeros para pagos.
- `2r1p`: 2 cajeros para retiros y 1 cajero para pagos.

## Supuestos de la simulacion

- La jornada simulada es de 8 horas, equivalentes a 480 minutos.
- Se ejecutan 10 replicas para obtener promedios y comparaciones.
- El 70% de los clientes realiza retiros.
- El 30% de los clientes realiza pagos.
- Los tiempos entre llegadas y los tiempos de servicio se generan con distribucion exponencial.
- Los usuarios se clasifican como `Rapido`, `Normal`, `Lento` y `Muy lento`.
- Se fija una semilla aleatoria para facilitar la reproducibilidad de los resultados.

## Resultados generados

Los archivos de salida se guardan en:

```text
resultados_simulacion/
```

Archivos Excel generados:

- `resultados_simulacion_punto1.xlsx`
- `punto2_promedio_usuarios_por_tipo.xlsx`
- `punto3_usuarios_por_replica.xlsx`
- `punto3_resumen_replicas_minimas.xlsx`
- `punto4_necesidad_nuevo_cajero.xlsx`
- `punto4_tiempos_espera_por_tipo.xlsx`
- `punto5_comparacion_configuraciones.xlsx`

Graficas generadas:

- `grafica_punto1_tiempos_cajeros.png`
- `grafica_punto2_promedio_usuarios.png`
- `grafica_punto3_usuarios_por_replica.png`
- `grafica_punto4_analisis.png`
- `grafica_punto5_comparacion_configuraciones.png`

## Descripcion de los puntos analizados

### Punto 1: tiempo promedio por cajero

Calcula el tiempo promedio de servicio de cada cajero e identifica el cajero mas rapido y el mas lento.

### Punto 2: promedio de usuarios por tipo

Agrupa los usuarios por tipo de transaccion y tipo de usuario, calculando el promedio diario y la desviacion estandar.

### Punto 3: usuarios por replica

Genera una tabla con el total de usuarios atendidos en cada replica y determina cuales replicas tuvieron la menor cantidad de usuarios por categoria.

### Punto 4: necesidad de un nuevo cajero

Evalua el tiempo promedio de espera, los tiempos por tipo de usuario y la utilizacion de los cajeros para decidir si se requiere agregar un cajero adicional.

### Punto 5: comparacion de configuraciones

Compara tres escenarios de atencion:

- 3 cajas mixtas.
- 1 caja para retiros y 2 cajas para pagos.
- 2 cajas para retiros y 1 caja para pagos.

La mejor configuracion se elige segun el menor tiempo promedio de espera.

## Estructura esperada

```text
Evidencia 3/
|-- Actividad4Bancos.py
|-- README.md
|-- resultados_simulacion/
    |-- archivos .xlsx
    |-- graficas .png
```

La carpeta `resultados_simulacion` se crea automaticamente al ejecutar el programa.

## Autor

Proyecto academico de simulacion desarrollado para la Evidencia 3.
