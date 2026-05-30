import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from pathlib import Path

# Definir ruta base donde se guardarán los archivos
ruta_base = Path("resultados_simulacion")
ruta_base.mkdir(parents=True, exist_ok=True)
# Crear la carpeta si no existe
os.makedirs(ruta_base, exist_ok=True)

# Fijar semilla para reproducibilidad
np.random.seed(42)


class SimulacionBanco:
    def __init__(self, num_cajeros=3, horas_operacion=8, configuracion="mixto"):
        """
        Inicializa la simulación del banco.

        Parámetros:
        - num_cajeros: número de cajeros disponibles
        - horas_operacion: horas que opera el banco al día
        - configuracion: "mixto", "1r2p" (1 retiro + 2 pagos), "2r1p" (2 retiros + 1 pago)
        """
        self.num_cajeros = num_cajeros
        self.tiempo_simulacion = horas_operacion * 60  # convertir a minutos
        self.configuracion = configuracion

        # Configuración de cajeros especializados
        self.cajeros_retiro = []  # Índices de cajeros que solo atienden retiros
        self.cajeros_pago = []  # Índices de cajeros que solo atienden pagos

        if configuracion == "1r2p":
            # 1 cajero para retiros (índice 0), 2 para pagos (índices 1,2)
            self.cajeros_retiro = [0]
            self.cajeros_pago = [1, 2]
        elif configuracion == "2r1p":
            # 2 cajeros para retiros (índices 0,1), 1 para pagos (índice 2)
            self.cajeros_retiro = [0, 1]
            self.cajeros_pago = [2]
        else:  # "mixto"
            # Todos atienden todo
            self.cajeros_retiro = list(range(num_cajeros))
            self.cajeros_pago = list(range(num_cajeros))

        # Probabilidades de tipo de acción
        self.prob_retiro = 0.7
        self.prob_pago = 0.3

        # Probabilidades de tipo de usuario dentro de cada acción
        self.prob_usuario_retiro = [0.23, 0.40, 0.17, 0.20]  # Rápido, Normal, Lento, Muy lento
        self.prob_usuario_pago = [0.10, 0.20, 0.30, 0.40]

        # Tiempos de servicio (media en minutos)
        self.servicio_retiro = [1, 2, 3, 4]
        self.servicio_pago = [3, 3, 5, 7]

        # Tiempos entre llegadas (media en minutos)
        self.llegada_retiro = [1, 2, 3, 3]
        self.llegada_pago = [1, 2, 3, 4]

        # Mapeo de tipos de usuario a nombres
        self.nombres_usuario = ["Rápido", "Normal", "Lento", "Muy lento"]

    def generar_tiempo_exponencial(self, media):
        """Genera un tiempo aleatorio con distribución exponencial."""
        return np.random.exponential(media)

    def generar_tipo_accion(self):
        """Determina si el cliente hace retiro o pago."""
        return "retiro" if np.random.random() < self.prob_retiro else "pago"

    def generar_tipo_usuario(self, tipo_accion):
        """
        Determina el tipo de usuario (0:Rápido, 1:Normal, 2:Lento, 3:Muy lento)
        según la acción.
        """
        if tipo_accion == "retiro":
            return np.random.choice([0, 1, 2, 3], p=self.prob_usuario_retiro)
        else:
            return np.random.choice([0, 1, 2, 3], p=self.prob_usuario_pago)

    def obtener_tiempo_servicio(self, tipo_accion, tipo_usuario):
        """Retorna la media del tiempo de servicio según acción y tipo."""
        if tipo_accion == "retiro":
            return self.servicio_retiro[tipo_usuario]
        else:
            return self.servicio_pago[tipo_usuario]

    def obtener_tiempo_llegada(self, tipo_accion, tipo_usuario):
        """Retorna la media del tiempo entre llegadas según acción y tipo."""
        if tipo_accion == "retiro":
            return self.llegada_retiro[tipo_usuario]
        else:
            return self.llegada_pago[tipo_usuario]

    def simular_dia(self, semilla=None):
        """Simula un día de operación del banco. Retorna DataFrame con clientes atendidos."""
        if semilla is not None:
            np.random.seed(semilla)

        # Inicializar estado de cajeros
        cajeros_ocupados = [False] * self.num_cajeros
        cajeros_tiempo_fin_servicio = [0] * self.num_cajeros

        # Cola de clientes: cada elemento es un diccionario
        cola = []

        # Lista para almacenar clientes atendidos
        clientes = []

        # Generar primera llegada
        tipo_accion = self.generar_tipo_accion()
        tipo_usuario = self.generar_tipo_usuario(tipo_accion)
        tiempo_prox_llegada = self.generar_tiempo_exponencial(
            self.obtener_tiempo_llegada(tipo_accion, tipo_usuario)
        )

        tiempo_actual = 0

        while tiempo_actual < self.tiempo_simulacion:
            # Encontrar próximo evento: próxima llegada o próximo fin de servicio
            tiempos_futuros = [t for t in cajeros_tiempo_fin_servicio if t > tiempo_actual]
            tiempo_prox_fin_servicio = min(tiempos_futuros) if tiempos_futuros else float("inf")

            if tiempo_prox_llegada < tiempo_prox_fin_servicio:
                # ===== EVENTO: LLEGADA DE CLIENTE =====
                tiempo_actual = tiempo_prox_llegada

                # Registrar llegada
                cliente = {
                    "tiempo_llegada": tiempo_actual,
                    "tipo_accion": tipo_accion,
                    "tipo_usuario": tipo_usuario,
                }

                # Buscar cajero libre (según configuración)
                cajero_asignado = None

                # Determinar qué cajeros puede usar este cliente
                if tipo_accion == "retiro":
                    cajeros_permitidos = self.cajeros_retiro
                else:  # pago
                    cajeros_permitidos = self.cajeros_pago

                # Buscar cajero libre entre los permitidos
                for i in cajeros_permitidos:
                    if cajeros_tiempo_fin_servicio[i] <= tiempo_actual:
                        cajero_asignado = i
                        break

                if cajero_asignado is not None:
                    # Atender inmediatamente
                    tiempo_servicio = self.generar_tiempo_exponencial(
                        self.obtener_tiempo_servicio(tipo_accion, tipo_usuario)
                    )
                    cliente["cajero"] = cajero_asignado
                    cliente["tiempo_inicio_servicio"] = tiempo_actual
                    cliente["tiempo_fin_servicio"] = tiempo_actual + tiempo_servicio
                    cliente["tiempo_espera"] = 0
                    cliente["tiempo_servicio"] = tiempo_servicio
                    clientes.append(cliente)

                    # Actualizar cajero
                    cajeros_tiempo_fin_servicio[cajero_asignado] = tiempo_actual + tiempo_servicio
                else:
                    # Todos los cajeros ocupados, agregar a cola
                    cola.append(cliente)

                # Generar próxima llegada
                tipo_accion = self.generar_tipo_accion()
                tipo_usuario = self.generar_tipo_usuario(tipo_accion)
                tiempo_prox_llegada = tiempo_actual + self.generar_tiempo_exponencial(
                    self.obtener_tiempo_llegada(tipo_accion, tipo_usuario)
                )

            else:
                # ===== EVENTO: FIN DE SERVICIO =====
                tiempo_actual = tiempo_prox_fin_servicio

                # Atender siguiente cliente en cola si hay
                while cola:
                    # Tomar el primer cliente de la cola
                    cliente_cola = cola[0]

                    # Determinar qué cajeros puede usar este cliente
                    if cliente_cola["tipo_accion"] == "retiro":
                        cajeros_permitidos = self.cajeros_retiro
                    else:
                        cajeros_permitidos = self.cajeros_pago

                    # Buscar cajero disponible
                    cajero_libre = None
                    for i in cajeros_permitidos:
                        if cajeros_tiempo_fin_servicio[i] <= tiempo_actual:
                            cajero_libre = i
                            break

                    if cajero_libre is not None:
                        # Sacar cliente de la cola
                        cola.pop(0)

                        # Atender
                        tiempo_servicio = self.generar_tiempo_exponencial(
                            self.obtener_tiempo_servicio(
                                cliente_cola["tipo_accion"],
                                cliente_cola["tipo_usuario"],
                            )
                        )
                        cliente_cola["cajero"] = cajero_libre
                        cliente_cola["tiempo_inicio_servicio"] = tiempo_actual
                        cliente_cola["tiempo_fin_servicio"] = tiempo_actual + tiempo_servicio
                        cliente_cola["tiempo_espera"] = tiempo_actual - cliente_cola["tiempo_llegada"]
                        cliente_cola["tiempo_servicio"] = tiempo_servicio
                        clientes.append(cliente_cola)

                        # Actualizar cajero
                        cajeros_tiempo_fin_servicio[cajero_libre] = tiempo_actual + tiempo_servicio
                    else:
                        # No hay cajero disponible, salir del while
                        break

        return pd.DataFrame(clientes)

    def ejecutar_replicas(self, num_replicas=10):
        """Ejecuta múltiples réplicas de la simulación."""
        resultados = []
        for i in range(num_replicas):
            print(f"Ejecutando réplica {i+1}/{num_replicas}...")
            df = self.simular_dia(semilla=i)
            df["replica"] = i + 1
            resultados.append(df)

        return pd.concat(resultados, ignore_index=True)

    def calcular_punto1(self, df_resultados):
        """
        Punto 1: Identificar cajero con menor y mayor tiempo promedio de atención.
        """
        tiempos_por_cajero = df_resultados.groupby("cajero")["tiempo_servicio"].mean()

        cajero_menor = tiempos_por_cajero.idxmin()
        tiempo_menor = tiempos_por_cajero.min()
        cajero_mayor = tiempos_por_cajero.idxmax()
        tiempo_mayor = tiempos_por_cajero.max()

        resultados = {
            "cajero_menor_tiempo": int(cajero_menor),
            "tiempo_menor": tiempo_menor,
            "cajero_mayor_tiempo": int(cajero_mayor),
            "tiempo_mayor": tiempo_mayor,
            "tiempos_por_cajero": tiempos_por_cajero.to_dict(),
        }

        return resultados

    def calcular_punto2(self, df_resultados):
        """
        Punto 2: Establecer el promedio de usuarios de cada tipo en la totalidad de cajeros.
        """
        mapa_usuario = {0: "Rápido", 1: "Normal", 2: "Lento", 3: "Muy lento"}
        df_resultados["nombre_usuario"] = df_resultados["tipo_usuario"].map(mapa_usuario)

        conteo_por_replica = (
            df_resultados.groupby(["replica", "tipo_accion", "nombre_usuario"])
            .size()
            .reset_index(name="conteo")
        )

        promedio_por_tipo = (
            conteo_por_replica.groupby(["tipo_accion", "nombre_usuario"])["conteo"]
            .mean()
            .reset_index()
        )
        promedio_por_tipo = promedio_por_tipo.rename(columns={"conteo": "promedio_usuarios_por_dia"})

        desviacion_por_tipo = (
            conteo_por_replica.groupby(["tipo_accion", "nombre_usuario"])["conteo"]
            .std()
            .reset_index()
        )
        desviacion_por_tipo = desviacion_por_tipo.rename(columns={"conteo": "desviacion_std"})

        resultado = pd.merge(promedio_por_tipo, desviacion_por_tipo, on=["tipo_accion", "nombre_usuario"])

        orden_accion = {"retiro": 1, "pago": 2}
        resultado["orden_accion"] = resultado["tipo_accion"].map(orden_accion)
        resultado = resultado.sort_values(["orden_accion", "nombre_usuario"]).drop("orden_accion", axis=1)

        return resultado

    def calcular_punto3(self, df_resultados):
        """
        Punto 3: Determinar el total de usuarios de cada tipo en cada réplica
        y detallar la réplica con menor cantidad de usuarios por tipo.
        """
        mapa_usuario = {0: "Rápido", 1: "Normal", 2: "Lento", 3: "Muy lento"}
        df_resultados["nombre_usuario"] = df_resultados["tipo_usuario"].map(mapa_usuario)

        tabla_detallada = (
            df_resultados.groupby(["replica", "tipo_accion", "nombre_usuario"])
            .size()
            .reset_index(name="total_usuarios")
        )

        # Identificar la réplica con menor cantidad de usuarios por cada tipo
        replicas_minimas = {}
        tipos = tabla_detallada["tipo_accion"].unique()
        nombres = tabla_detallada["nombre_usuario"].unique()

        for tipo_accion in tipos:
            for nombre_usuario in nombres:
                subset = tabla_detallada[
                    (tabla_detallada["tipo_accion"] == tipo_accion)
                    & (tabla_detallada["nombre_usuario"] == nombre_usuario)
                ]
                if len(subset) > 0:
                    fila_min = subset.loc[subset["total_usuarios"].idxmin()]
                    clave = f"{tipo_accion}_{nombre_usuario}"
                    replicas_minimas[clave] = {
                        "replica": int(fila_min["replica"]),
                        "total_usuarios": int(fila_min["total_usuarios"]),
                    }

        return tabla_detallada, replicas_minimas

    def calcular_punto4(self, df_resultados):
        """
        Punto 4: Definir si es necesario crear un nuevo cajero basado en tiempos de espera.
        """
        # Calcular tiempo de espera promedio general
        tiempo_espera_general = df_resultados["tiempo_espera"].mean()

        # Calcular tiempo de espera por tipo de usuario
        mapa_usuario = {0: "Rápido", 1: "Normal", 2: "Lento", 3: "Muy lento"}
        df_resultados["nombre_usuario"] = df_resultados["tipo_usuario"].map(mapa_usuario)
        df_resultados["tipo_completo"] = df_resultados["tipo_accion"] + "_" + df_resultados["nombre_usuario"]

        tiempo_espera_por_tipo = (
            df_resultados.groupby("tipo_completo")["tiempo_espera"]
            .mean()
            .sort_values(ascending=False)
        )

        # Calcular utilización de cada cajero
        tiempo_total = self.tiempo_simulacion  # 480 minutos por día
        tiempo_ocupado_por_cajero = (
            df_resultados.groupby(["replica", "cajero"])["tiempo_servicio"]
            .sum()
            .reset_index()
        )
        tiempo_ocupado_promedio = tiempo_ocupado_por_cajero.groupby("cajero")["tiempo_servicio"].mean()
        utilizacion_por_cajero = (tiempo_ocupado_promedio / tiempo_total) * 100

        # Determinar si necesita nuevo cajero
        necesita_nuevo_cajero = False
        justificacion = []

        if tiempo_espera_general > 5:
            necesita_nuevo_cajero = True
            justificacion.append(f"Tiempo de espera general de {tiempo_espera_general:.2f} minutos > 5 minutos")

        max_espera_por_tipo = tiempo_espera_por_tipo.max()
        if max_espera_por_tipo > 10:
            necesita_nuevo_cajero = True
            tipo_peor = tiempo_espera_por_tipo.idxmax()
            justificacion.append(f"Usuarios '{tipo_peor}' esperan {max_espera_por_tipo:.2f} minutos > 10 minutos")

        utilizacion_promedio = utilizacion_por_cajero.mean()
        if utilizacion_promedio > 85:
            necesita_nuevo_cajero = True
            justificacion.append(f"Utilización promedio del {utilizacion_promedio:.1f}% > 85%")

        if not justificacion:
            justificacion.append(f"Sistema operando correctamente. Espera: {tiempo_espera_general:.2f} min, Utilización: {utilizacion_promedio:.1f}%")

        resultados = {
            "tiempo_espera_promedio_general": tiempo_espera_general,
            "tiempo_espera_por_tipo": tiempo_espera_por_tipo.to_dict(),
            "utilizacion_por_cajero": utilizacion_por_cajero.to_dict(),
            "utilizacion_promedio": utilizacion_promedio,
            "necesita_nuevo_cajero": necesita_nuevo_cajero,
            "justificacion": " | ".join(justificacion),
        }

        return resultados

    def comparar_configuraciones(self, num_replicas=10):
        """
        Compara las 3 configuraciones de cajeros.
        """
        configuraciones = ["mixto", "1r2p", "2r1p"]
        nombres_config = {
            "mixto": "3 cajas mixtas",
            "1r2p": "1 caja retiros + 2 cajas pagos",
            "2r1p": "2 cajas retiros + 1 caja pagos",
        }

        resultados_comparativa = []

        for config in configuraciones:
            print(f"\n📊 Simulando configuración: {nombres_config[config]}")
            print("-" * 50)

            sim_config = SimulacionBanco(num_cajeros=3, horas_operacion=8, configuracion=config)
            resultados_config = sim_config.ejecutar_replicas(num_replicas=num_replicas)

            tiempo_espera_promedio = resultados_config["tiempo_espera"].mean()
            tiempo_servicio_promedio = resultados_config["tiempo_servicio"].mean()
            total_clientes = len(resultados_config)
            clientes_por_dia = total_clientes / num_replicas

            mapa_usuario = {0: "Rápido", 1: "Normal", 2: "Lento", 3: "Muy lento"}
            resultados_config["nombre_usuario"] = resultados_config["tipo_usuario"].map(mapa_usuario)

            tiempo_espera_retiro = resultados_config[resultados_config["tipo_accion"] == "retiro"]["tiempo_espera"].mean()
            tiempo_espera_pago = resultados_config[resultados_config["tipo_accion"] == "pago"]["tiempo_espera"].mean()

            resultados_comparativa.append({
                "configuracion": nombres_config[config],
                "codigo": config,
                "tiempo_espera_promedio_min": tiempo_espera_promedio,
                "tiempo_servicio_promedio_min": tiempo_servicio_promedio,
                "clientes_por_dia": clientes_por_dia,
                "tiempo_espera_retiros_min": tiempo_espera_retiro,
                "tiempo_espera_pagos_min": tiempo_espera_pago,
            })

        return pd.DataFrame(resultados_comparativa)

    def generar_graficas(self, df_resultados, p1, p2, p3_tabla, p4, df_comparativa, ruta_base):
        """
        Genera todas las gráficas de los 5 puntos, las guarda como imágenes Y las muestra en pantalla.
        """
        # ============ GRÁFICA PUNTO 1 ============
        plt.figure(figsize=(10, 6))
        cajeros = list(p1["tiempos_por_cajero"].keys())
        tiempos = list(p1["tiempos_por_cajero"].values())

        colores = [
            ("green" if i == p1["cajero_menor_tiempo"] else "red" if i == p1["cajero_mayor_tiempo"] else "steelblue")
            for i in cajeros
        ]

        plt.bar(cajeros, tiempos, color=colores)
        plt.xlabel("Número de Cajero", fontsize=12)
        plt.ylabel("Tiempo Promedio de Atención (minutos)", fontsize=12)
        plt.title("Punto 1: Tiempo Promedio de Atención por Cajero\n(Verde = más rápido, Rojo = más lento)", fontsize=14)
        plt.xticks(cajeros)
        plt.grid(axis="y", alpha=0.3)

        for i, (cajero, tiempo) in enumerate(zip(cajeros, tiempos)):
            plt.text(i, tiempo + 0.05, f"{tiempo:.3f}", ha="center", fontweight="bold")

        plt.tight_layout()
        plt.savefig(f"{ruta_base}\\grafica_punto1_tiempos_cajeros.png", dpi=150, bbox_inches="tight")
        plt.show()
        plt.close()
        print(f"   ✅ Gráfica Punto 1 guardada: grafica_punto1_tiempos_cajeros.png")

        # ============ GRÁFICA PUNTO 2 ============
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        tipos_retiro = p2[p2["tipo_accion"] == "retiro"]
        tipos_pago = p2[p2["tipo_accion"] == "pago"]

        x_retiro = range(len(tipos_retiro))
        x_pago = range(len(tipos_pago))

        ax1.bar(x_retiro, tipos_retiro["promedio_usuarios_por_dia"], color="steelblue", alpha=0.8)
        ax1.set_xlabel("Tipo de Usuario (Retiros)", fontsize=11)
        ax1.set_ylabel("Promedio de Usuarios por Día", fontsize=11)
        ax1.set_title("Punto 2: Promedio de Usuarios - Retiros", fontsize=12)
        ax1.set_xticks(x_retiro)
        ax1.set_xticklabels(tipos_retiro["nombre_usuario"], rotation=45)
        ax1.grid(axis="y", alpha=0.3)

        ax2.bar(x_pago, tipos_pago["promedio_usuarios_por_dia"], color="darkorange", alpha=0.8)
        ax2.set_xlabel("Tipo de Usuario (Pagos)", fontsize=11)
        ax2.set_ylabel("Promedio de Usuarios por Día", fontsize=11)
        ax2.set_title("Punto 2: Promedio de Usuarios - Pagos", fontsize=12)
        ax2.set_xticks(x_pago)
        ax2.set_xticklabels(tipos_pago["nombre_usuario"], rotation=45)
        ax2.grid(axis="y", alpha=0.3)

        plt.suptitle("Distribución Promedio de Usuarios por Tipo", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(f"{ruta_base}\\grafica_punto2_promedio_usuarios.png", dpi=150, bbox_inches="tight")
        plt.show()
        plt.close()
        print(f"   ✅ Gráfica Punto 2 guardada: grafica_punto2_promedio_usuarios.png")

        # ============ GRÁFICA PUNTO 3 ============
        total_por_replica = p3_tabla.groupby("replica")["total_usuarios"].sum()

        plt.figure(figsize=(12, 6))
        plt.bar(total_por_replica.index, total_por_replica.values, color="steelblue", alpha=0.7)
        plt.xlabel("Número de Réplica", fontsize=12)
        plt.ylabel("Total de Usuarios", fontsize=12)
        plt.title("Punto 3: Total de Usuarios por Réplica", fontsize=14)
        plt.xticks(total_por_replica.index)
        plt.grid(axis="y", alpha=0.3)

        replica_min = total_por_replica.idxmin()
        valor_min = total_por_replica.min()
        plt.bar(replica_min, valor_min, color="red", alpha=0.8, label=f"Réplica con menos usuarios: {replica_min} ({valor_min})")
        plt.legend()

        for i, (replica, total) in enumerate(total_por_replica.items()):
            plt.text(replica, total + 2, str(total), ha="center", fontsize=9)

        plt.tight_layout()
        plt.savefig(f"{ruta_base}\\grafica_punto3_usuarios_por_replica.png", dpi=150, bbox_inches="tight")
        plt.show()
        plt.close()
        print(f"   ✅ Gráfica Punto 3 guardada: grafica_punto3_usuarios_por_replica.png")

        # ============ GRÁFICA PUNTO 4 ============
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        tipos = list(p4["tiempo_espera_por_tipo"].keys())
        tiempos_espera = list(p4["tiempo_espera_por_tipo"].values())

        colores_espera = ["#dc3545" if t > 0.5 else "#28a745" for t in tiempos_espera]
        ax1.barh(tipos, tiempos_espera, color=colores_espera)
        ax1.set_xlabel("Tiempo de Espera (minutos)", fontsize=11)
        ax1.set_title("Punto 4: Tiempo de Espera por Tipo de Usuario", fontsize=12)
        ax1.axvline(x=0.5, color="red", linestyle="--", label="Umbral 0.5 min")
        ax1.legend()

        cajeros = list(p4["utilizacion_por_cajero"].keys())
        utilizacion = list(p4["utilizacion_por_cajero"].values())

        ax2.bar(cajeros, utilizacion, color="steelblue")
        ax2.axhline(y=85, color="red", linestyle="--", label="Umbral 85%")
        ax2.set_xlabel("Cajero", fontsize=11)
        ax2.set_ylabel("Utilización (%)", fontsize=11)
        ax2.set_title("Punto 4: Utilización de Cajeros", fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.legend()

        for i, (cajero, uso) in enumerate(zip(cajeros, utilizacion)):
            ax2.text(i, uso + 2, f"{uso:.1f}%", ha="center", fontweight="bold")

        plt.suptitle("Análisis de Tiempos de Espera y Utilización", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(f"{ruta_base}\\grafica_punto4_analisis.png", dpi=150, bbox_inches="tight")
        plt.show()
        plt.close()
        print(f"   ✅ Gráfica Punto 4 guardada: grafica_punto4_analisis.png")

        # ============ GRÁFICA PUNTO 5 ============
        plt.figure(figsize=(12, 6))

        configs = df_comparativa["configuracion"]
        tiempos_espera = df_comparativa["tiempo_espera_promedio_min"]
        tiempos_retiros = df_comparativa["tiempo_espera_retiros_min"]
        tiempos_pagos = df_comparativa["tiempo_espera_pagos_min"]

        x = range(len(configs))
        width = 0.25

        plt.bar([i - width for i in x], tiempos_retiros, width, label="Retiros", color="steelblue")
        plt.bar(x, tiempos_pagos, width, label="Pagos", color="darkorange")
        plt.bar([i + width for i in x], tiempos_espera, width, label="Promedio General", color="green", alpha=0.7)

        plt.xlabel("Configuración", fontsize=12)
        plt.ylabel("Tiempo de Espera (minutos)", fontsize=12)
        plt.title("Punto 5: Comparación de Tiempos de Espera por Configuración", fontsize=14)
        plt.xticks(x, configs, rotation=15, ha="right")
        plt.legend()
        plt.grid(axis="y", alpha=0.3)

        for i in x:
            plt.text(i - width, tiempos_retiros[i] + 0.1, f"{tiempos_retiros[i]:.2f}", ha="center", fontsize=8)
            plt.text(i, tiempos_pagos[i] + 0.1, f"{tiempos_pagos[i]:.2f}", ha="center", fontsize=8)
            plt.text(i + width, tiempos_espera[i] + 0.1, f"{tiempos_espera[i]:.2f}", ha="center", fontsize=8, fontweight="bold")

        plt.tight_layout()
        plt.savefig(f"{ruta_base}\\grafica_punto5_comparacion_configuraciones.png", dpi=150, bbox_inches="tight")
        plt.show()
        plt.close()
        print(f"   ✅ Gráfica Punto 5 guardada: grafica_punto5_comparacion_configuraciones.png")

        print("\n📊 Todas las gráficas han sido generadas y mostradas en pantalla!")
        print(f"📁 También se guardaron en: {ruta_base}")


# ============ EJECUCIÓN PRINCIPAL ============
if __name__ == "__main__":
    print("=" * 60)
    print("SIMULACIÓN DEL BANCO DE COLOMBIA")
    print("=" * 60)

    # Crear instancia de la simulación
    sim = SimulacionBanco(num_cajeros=3, horas_operacion=8)

    # Ejecutar 10 réplicas
    print("\n📊 Ejecutando 10 réplicas de 8 horas cada una...\n")
    resultados = sim.ejecutar_replicas(num_replicas=10)

    # ============ PUNTO 1 ============
    print("\n" + "=" * 60)
    print("PUNTO 1: Cajero con menor y mayor tiempo promedio de atención")
    print("=" * 60)

    p1 = sim.calcular_punto1(resultados)

    print(f"\n📈 Tiempo promedio de atención por cajero:")
    for cajero, tiempo in p1["tiempos_por_cajero"].items():
        print(f"   Cajero {cajero}: {tiempo:.4f} minutos")

    print(f"\n✅ Cajero con MENOR tiempo promedio de atención: Cajero {p1['cajero_menor_tiempo']} ({p1['tiempo_menor']:.4f} minutos)")
    print(f"❌ Cajero con MAYOR tiempo promedio de atención: Cajero {p1['cajero_mayor_tiempo']} ({p1['tiempo_mayor']:.4f} minutos)")

    # Estadísticas adicionales
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS ADICIONALES")
    print("=" * 60)

    total_clientes = len(resultados)
    print(f"\n👥 Total de clientes atendidos en 10 réplicas: {total_clientes}")
    print(f"📊 Promedio de clientes por día: {total_clientes/10:.1f}")

    tiempo_espera_promedio = resultados["tiempo_espera"].mean()
    print(f"⏱️  Tiempo de espera promedio en cola: {tiempo_espera_promedio:.4f} minutos")

    # Guardar resultados Punto 1
    resultados_formateado = resultados.copy()
    resultados_formateado["tiempo_servicio"] = resultados_formateado["tiempo_servicio"].round(4)
    resultados_formateado["tiempo_espera"] = resultados_formateado["tiempo_espera"].round(4)
    resultados_formateado["tiempo_inicio_servicio"] = resultados_formateado["tiempo_inicio_servicio"].round(4)
    resultados_formateado["tiempo_fin_servicio"] = resultados_formateado["tiempo_fin_servicio"].round(4)

    resultados_formateado.to_excel(f"{ruta_base}\\resultados_simulacion_punto1.xlsx", index=False)
    print(f"\n💾 Resultados guardados en: {ruta_base}\\resultados_simulacion_punto1.xlsx")

    print("\n" + "=" * 60)
    print("✅ PUNTO 1 COMPLETADO")
    print("=" * 60)

    # ============ PUNTO 2 ============
    print("\n" + "=" * 60)
    print("PUNTO 2: Promedio de usuarios de cada tipo en todos los cajeros")
    print("=" * 60)

    p2 = sim.calcular_punto2(resultados)

    print("\n📊 Promedio de usuarios por día (según tipo de acción y tipo de usuario):")
    print("-" * 60)

    for _, row in p2.iterrows():
        accion = "Retiro" if row["tipo_accion"] == "retiro" else "Pago"
        print(f"   {accion} - {row['nombre_usuario']:10s}: {row['promedio_usuarios_por_dia']:6.2f} ± {row['desviacion_std']:.2f} usuarios/día")

    total_retiros = p2[p2["tipo_accion"] == "retiro"]["promedio_usuarios_por_dia"].sum()
    total_pagos = p2[p2["tipo_accion"] == "pago"]["promedio_usuarios_por_dia"].sum()

    print(f"\n   Total Retiros: {total_retiros:.2f} usuarios/día")
    print(f"   Total Pagos:   {total_pagos:.2f} usuarios/día")
    print(f"   Total General: {total_retiros + total_pagos:.2f} usuarios/día")

    print(f"\n📊 Proporción observada:")
    print(f"   Retiros: {(total_retiros/(total_retiros+total_pagos)*100):.1f}% (esperado 70%)")
    print(f"   Pagos:   {(total_pagos/(total_retiros+total_pagos)*100):.1f}% (esperado 30%)")

    # Guardar resultado Punto 2
    p2_formateado = p2.copy()
    p2_formateado["promedio_usuarios_por_dia"] = p2_formateado["promedio_usuarios_por_dia"].round(2)
    p2_formateado["desviacion_std"] = p2_formateado["desviacion_std"].round(2)

    p2_formateado.to_excel(f"{ruta_base}\\punto2_promedio_usuarios_por_tipo.xlsx", index=False)
    print(f"\n💾 Resultados del Punto 2 guardados en: {ruta_base}\\punto2_promedio_usuarios_por_tipo.xlsx")

    # ============ PUNTO 3 ============
    print("\n" + "=" * 60)
    print("PUNTO 3: Total de usuarios de cada tipo en cada réplica")
    print("=" * 60)

    p3_tabla, p3_minimos = sim.calcular_punto3(resultados)

    # Pivotar tabla para mejor visualización
    tabla_pivot = p3_tabla.pivot_table(
        index="replica",
        columns=["tipo_accion", "nombre_usuario"],
        values="total_usuarios",
        fill_value=0,
    )
    tabla_pivot.columns = [f"{accion}_{nombre}" for accion, nombre in tabla_pivot.columns]

    print("\n📊 Total de usuarios por tipo en cada réplica:")
    print("-" * 80)
    print(tabla_pivot.to_string())

    # Guardar tabla completa
    tabla_pivot.to_excel(f"{ruta_base}\\punto3_usuarios_por_replica.xlsx")
    print(f"\n💾 Tabla completa guardada en: {ruta_base}\\punto3_usuarios_por_replica.xlsx")

    # Mostrar réplica con menos usuarios por cada tipo
    print("\n" + "=" * 60)
    print("📌 Réplica con MENOR cantidad de usuarios por cada tipo:")
    print("-" * 60)

    for tipo, info in p3_minimos.items():
        tipo_mostrar = tipo.replace("_", " - ").capitalize()
        print(f"   {tipo_mostrar:30s}: Réplica {info['replica']} ({info['total_usuarios']} usuarios)")

    # Réplica con menor total general
    total_por_replica = p3_tabla.groupby("replica")["total_usuarios"].sum()
    replica_menor_total = total_por_replica.idxmin()
    menor_total = total_por_replica.min()

    print("\n" + "=" * 60)
    print("📊 RESUMEN GENERAL DEL PUNTO 3")
    print("=" * 60)
    print(f"\n📌 Réplica con MENOS usuarios en TOTAL: Réplica {replica_menor_total} ({menor_total} usuarios en total)")

    print(f"\n📌 Desglose de la Réplica {replica_menor_total} (la que menos usuarios tuvo):")
    print("-" * 60)
    replica_min = p3_tabla[p3_tabla["replica"] == replica_menor_total]
    for _, row in replica_min.iterrows():
        accion = "Retiro" if row["tipo_accion"] == "retiro" else "Pago"
        print(f"   {accion} - {row['nombre_usuario']:10s}: {row['total_usuarios']} usuarios")

    # Guardar resumen
    resumen_p3 = pd.DataFrame([
        {"tipo_usuario": tipo, "replica_menor_usuarios": info["replica"], "cantidad_menor": info["total_usuarios"]}
        for tipo, info in p3_minimos.items()
    ])
    resumen_p3.to_excel(f"{ruta_base}\\punto3_resumen_replicas_minimas.xlsx", index=False)
    print(f"\n💾 Resumen de réplicas mínimas guardado en: {ruta_base}\\punto3_resumen_replicas_minimas.xlsx")

    # ============ PUNTO 4 ============
    print("\n" + "=" * 60)
    print("PUNTO 4: ¿Es necesario crear un nuevo cajero?")
    print("=" * 60)

    p4 = sim.calcular_punto4(resultados)

    print(f"\n📊 ESTADÍSTICAS DE ESPERA:")
    print(f"   Tiempo de espera promedio general: {p4['tiempo_espera_promedio_general']:.2f} minutos")

    print(f"\n📊 TIEMPO DE ESPERA POR TIPO DE USUARIO:")
    print("-" * 60)
    for tipo, tiempo in p4["tiempo_espera_por_tipo"].items():
        tipo_mostrar = tipo.replace("_", " - ").replace("retiro", "Retiro").replace("pago", "Pago")
        print(f"   {tipo_mostrar:35s}: {tiempo:.2f} minutos")

    print(f"\n📊 UTILIZACIÓN DE CAJEROS:")
    print("-" * 60)
    for cajero, uso in p4["utilizacion_por_cajero"].items():
        print(f"   Cajero {cajero}: {uso:.1f}% de ocupación")
    print(f"   Promedio general: {p4['utilizacion_promedio']:.1f}%")

    print(f"\n📊 CONCLUSIÓN DEL ANÁLISIS:")
    print("-" * 60)
    if p4["necesita_nuevo_cajero"]:
        print(f"   ⚠️ SÍ es necesario crear un NUEVO CAJERO")
    else:
        print(f"   ✅ NO es necesario crear un nuevo cajero")
    print(f"   📝 Justificación: {p4['justificacion']}")

    # Guardar resultados Punto 4
    p4_resumen = pd.DataFrame([
        {"Metrica": "Tiempo espera promedio general (minutos)", "Valor": p4["tiempo_espera_promedio_general"]},
        {"Metrica": "Utilizacion promedio cajeros (%)", "Valor": p4["utilizacion_promedio"]},
        {"Metrica": "Necesita nuevo cajero", "Valor": "Sí" if p4["necesita_nuevo_cajero"] else "No"},
        {"Metrica": "Justificacion", "Valor": p4["justificacion"]}
    ])
    p4_resumen.to_excel(f"{ruta_base}\\punto4_necesidad_nuevo_cajero.xlsx", index=False)
    print(f"\n💾 Resultados del Punto 4 guardados en: {ruta_base}\\punto4_necesidad_nuevo_cajero.xlsx")

    p4_tipos = pd.DataFrame([
        {"Tipo_usuario": tipo, "Tiempo_espera_minutos": tiempo}
        for tipo, tiempo in p4["tiempo_espera_por_tipo"].items()
    ])
    p4_tipos.to_excel(f"{ruta_base}\\punto4_tiempos_espera_por_tipo.xlsx", index=False)

    # ============ PUNTO 5 ============
    print("\n" + "=" * 60)
    print("PUNTO 5: Comparación de configuraciones de cajeros")
    print("=" * 60)
    print("\n📊 Configuraciones a evaluar:")
    print("   1. 3 cajas mixtas (todos atienden todo)")
    print("   2. 1 caja exclusiva para retiros + 2 cajas para pagos")
    print("   3. 2 cajas exclusivas para retiros + 1 caja para pagos")

    df_comparativa = sim.comparar_configuraciones(num_replicas=10)

    print("\n" + "=" * 60)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("=" * 60)
    print(df_comparativa.to_string(index=False))

    mejor_fila = df_comparativa.loc[df_comparativa["tiempo_espera_promedio_min"].idxmin()]
    mejor_config = mejor_fila["configuracion"]
    mejor_tiempo = mejor_fila["tiempo_espera_promedio_min"]

    print("\n" + "=" * 60)
    print("🎯 CONCLUSIÓN DEL PUNTO 5")
    print("=" * 60)
    print(f"\n✅ La MEJOR configuración es: {mejor_config}")
    print(f"   Tiempo de espera promedio: {mejor_tiempo:.2f} minutos")

    print("\n📊 Comparativa detallada:")
    print("-" * 60)
    for _, row in df_comparativa.iterrows():
        print(f"\n   {row['configuracion']}:")
        print(f"      - Tiempo de espera: {row['tiempo_espera_promedio_min']:.2f} min")
        print(f"      - Retiros esperan: {row['tiempo_espera_retiros_min']:.2f} min")
        print(f"      - Pagos esperan:   {row['tiempo_espera_pagos_min']:.2f} min")
        print(f"      - Clientes/día:    {row['clientes_por_dia']:.1f}")

    print("\n" + "=" * 60)
    print("📝 RECOMENDACIÓN FINAL PARA EL BANCO")
    print("=" * 60)

    if mejor_config == "3 cajas mixtas":
        print("\n✅ Mantener las 3 cajas mixtas (sin especialización)")
    elif mejor_config == "1 caja retiros + 2 cajas pagos":
        print("\n✅ Asignar 1 caja exclusiva para RETIROS y 2 cajas para PAGOS")
    else:
        print("\n✅ Asignar 2 cajas exclusivas para RETIROS y 1 caja para PAGOS")

    df_comparativa.to_excel(f"{ruta_base}\\punto5_comparacion_configuraciones.xlsx", index=False)
    print(f"\n💾 Resultados del Punto 5 guardados en: {ruta_base}\\punto5_comparacion_configuraciones.xlsx")

    # ============ GENERAR GRÁFICAS PARA EL INFORME ============
    print("\n" + "=" * 60)
    print("GENERANDO GRÁFICAS PARA EL INFORME")
    print("=" * 60)

    sim.generar_graficas(resultados, p1, p2, p3_tabla, p4, df_comparativa, ruta_base)

    print("\n" + "=" * 60)
    print("SIMULACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)