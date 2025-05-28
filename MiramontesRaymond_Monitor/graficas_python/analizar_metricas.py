import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import os
from datetime import datetime
import re

def analizar_metricas(archivo_csv='metricas.csv'):
    """
    Analiza los datos del archivo CSV de métricas y genera gráficas
    y un reporte de análisis.
    """
    print(f"Leyendo datos desde '{archivo_csv}'...")
    
    try:
        nombres_columnas = ['timestamp', 'cpu_usage', 'top_process', 'memory_mb', 'temperature_c', 'network_kb']
        
        df = pd.read_csv("C:/xampp/htdocs/zdr/monitor/monitor/target/debug/metricas.csv", 
                         header=None, 
                         names=nombres_columnas)
        
        print(f"Se cargaron {len(df)} registros.")
        print("Columnas asignadas al CSV:")
        print(df.columns.tolist())
        print("Primeras filas del CSV:")
        print(df.head())
        
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return
    
    print("Procesando datos...")
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    df['memory_mb'] = df['memory_mb'].astype(str).str.replace('MB', '').astype(float)
    df['network_kb'] = df['network_kb'].astype(str).str.replace('KB', '').astype(float)
    
    df['temperature_c'] = pd.to_numeric(df['temperature_c'], errors='coerce')
    
    df['cpu_usage'] = pd.to_numeric(df['cpu_usage'], errors='coerce')
    
    print("Analizando procesos...")
    extraer_analizar_procesos(df)
    
    os.makedirs('graficas', exist_ok=True)
    
    print("Generando gráficas...")
    crear_grafica_cpu(df)
    crear_grafica_memoria(df)
    crear_grafica_red(df)
    crear_grafica_temperatura(df)
    crear_grafica_correlaciones(df)
    crear_grafica_patrones_hora(df)
    
    print("Generando reporte de análisis...")
    generar_reporte_analisis(df)
    
    print("¡Análisis completado! Revisa las gráficas en el directorio 'graficas' y el reporte 'reporte_analisis.txt'")

def extraer_analizar_procesos(df):
    """Extrae y analiza información de los procesos desde la columna top_process"""
    procesos = {}
    
    for idx, row in df.iterrows():
        if pd.isna(row['top_process']):
            continue
            
        lineas_procesos = row['top_process'].split('\n')
        
        for i, linea in enumerate(lineas_procesos):
            if not linea.strip():
                continue
                
            match = re.search(r'(.*?)\s+\(PID:\s+(\d+)\):\s+([\d.]+)%', linea)
            if match:
                nombre_proceso = match.group(1).strip()
                pid = match.group(2)
                uso_cpu = float(match.group(3))
                
                if i == 0:
                    if nombre_proceso in procesos:
                        procesos[nombre_proceso]['count'] += 1
                        procesos[nombre_proceso]['total_cpu'] += uso_cpu
                    else:
                        procesos[nombre_proceso] = {
                            'count': 1,
                            'total_cpu': uso_cpu,
                            'highest_cpu': uso_cpu,
                            'timestamp': row['timestamp']
                        }
                elif nombre_proceso in procesos and uso_cpu > procesos[nombre_proceso]['highest_cpu']:
                    procesos[nombre_proceso]['highest_cpu'] = uso_cpu
                    procesos[nombre_proceso]['timestamp'] = row['timestamp']
    
    proceso_mas_frecuente = None
    max_count = 0
    for proceso, datos in procesos.items():
        if datos['count'] > max_count:
            max_count = datos['count']
            proceso_mas_frecuente = proceso
    
    proceso_max_cpu = None
    max_cpu = 0
    timestamp_max_cpu = None
    for proceso, datos in procesos.items():
        if datos['highest_cpu'] > max_cpu:
            max_cpu = datos['highest_cpu']
            proceso_max_cpu = proceso
            timestamp_max_cpu = datos['timestamp']
    
    df.attrs['proceso_mas_frecuente'] = proceso_mas_frecuente
    df.attrs['proceso_max_cpu'] = proceso_max_cpu
    df.attrs['valor_max_cpu'] = max_cpu
    df.attrs['timestamp_max_cpu'] = timestamp_max_cpu
    
    top_procesos = sorted(procesos.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    df.attrs['top_5_procesos'] = top_procesos

def crear_grafica_cpu(df):
    """Crea gráfica de uso de CPU con información de procesos"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    ax1.plot(df['timestamp'], df['cpu_usage'], 'r-', linewidth=1)
    
    avg_cpu = df['cpu_usage'].mean()
    ax1.axhline(y=avg_cpu, color='g', linestyle='--', alpha=0.7, 
               label=f'Promedio: {avg_cpu:.2f}%')
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    
    max_idx = df['cpu_usage'].idxmax()
    max_point = df.iloc[max_idx]
    ax1.plot(max_point['timestamp'], max_point['cpu_usage'], 'ro', markersize=5)
    ax1.annotate(f"Máximo: {max_point['cpu_usage']:.2f}%", 
                xy=(max_point['timestamp'], max_point['cpu_usage']),
                xytext=(10, 10), textcoords='offset points')
    
    ax1.set_title('Uso de CPU durante el período de monitoreo')
    ax1.set_ylabel('Uso de CPU (%)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    ax2.axis('off')
    
    proceso_mas_frecuente = df.attrs.get('proceso_mas_frecuente', "No disponible")
    proceso_max_cpu = df.attrs.get('proceso_max_cpu', "No disponible")
    valor_max_cpu = df.attrs.get('valor_max_cpu', 0)
    timestamp_max_cpu = df.attrs.get('timestamp_max_cpu', None)
    top_procesos = df.attrs.get('top_5_procesos', [])
    
    texto_info = f"Proceso #1 más frecuente durante las 48 horas: {proceso_mas_frecuente}\n\n"
    texto_info += f"Proceso con mayor pico de CPU: {proceso_max_cpu} ({valor_max_cpu:.2f}%)"
    if timestamp_max_cpu:
        texto_info += f" - {timestamp_max_cpu.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
    else:
        texto_info += "\n\n"
    
    texto_info += "Top 5 procesos más frecuentes:\n"
    for i, (proceso, datos) in enumerate(top_procesos, 1):
        porcentaje = (datos['count'] / len(df)) * 100
        texto_info += f"{i}. {proceso}: {porcentaje:.1f}% del tiempo ({datos['count']} muestras, pico: {datos['highest_cpu']:.2f}% CPU)\n"
    
    ax2.text(0.01, 0.95, texto_info, transform=ax2.transAxes, fontsize=10,
             verticalalignment='top', bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.5})
    
    plt.tight_layout()
    plt.savefig('graficas/cpu_usage.png')
    plt.close()

def crear_grafica_memoria(df):
    """Crea gráfica de uso de memoria"""
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['memory_mb'], 'b-', linewidth=1)
    
    avg_memory = df['memory_mb'].mean()
    plt.axhline(y=avg_memory, color='g', linestyle='--', alpha=0.7, 
                label=f'Promedio: {avg_memory:.2f} MB')
    
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    
    plt.title('Uso de Memoria durante el período de monitoreo')
    plt.xlabel('Fecha/Hora')
    plt.ylabel('Memoria (MB)')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    plt.savefig('graficas/memory_usage.png')
    plt.close()

def crear_grafica_red(df):
    """Crea gráfica de tráfico de red"""
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['network_kb'], 'm-', linewidth=1)
    
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    
    plt.title('Tráfico de Red durante el período de monitoreo')
    plt.xlabel('Fecha/Hora')
    plt.ylabel('Tráfico de Red (KB)')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('graficas/network_traffic.png')
    plt.close()

def crear_grafica_temperatura(df):
    """Crea gráfica de temperatura si hay datos disponibles"""
    if df['temperature_c'].notna().sum() > 0:
        plt.figure(figsize=(12, 6))
        temp_df = df[df['temperature_c'].notna()]
        plt.plot(temp_df['timestamp'], temp_df['temperature_c'], 'orange', linewidth=1)
        
        avg_temp = temp_df['temperature_c'].mean()
        plt.axhline(y=avg_temp, color='g', linestyle='--', alpha=0.7, 
                    label=f'Promedio: {avg_temp:.2f}°C')
        
        plt.axhline(y=70, color='r', linestyle='--', alpha=0.7, 
                    label='Zona de advertencia: 70°C')
        
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        
        plt.title('Temperatura del Sistema durante el período de monitoreo')
        plt.xlabel('Fecha/Hora')
        plt.ylabel('Temperatura (°C)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend()
        plt.savefig('graficas/temperature.png')
        plt.close()

def crear_grafica_correlaciones(df):
    """Crea matriz de correlación entre las métricas"""
    df_num = df[['cpu_usage', 'memory_mb', 'network_kb']].copy()
    if df['temperature_c'].notna().sum() > 0:
        df_num['temperature_c'] = df['temperature_c']
    
    corr = df_num.corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, 
                linewidths=.5, cbar_kws={"shrink": .8})
    plt.title('Matriz de Correlación entre Métricas del Sistema')
    plt.tight_layout()
    plt.savefig('graficas/correlacion.png')
    plt.close()

def crear_grafica_patrones_hora(df):
    """Crea gráficas de patrones por hora del día"""
    df['hour'] = df['timestamp'].dt.hour
    
    plt.figure(figsize=(12, 6))
    cpu_by_hour = df.groupby('hour')['cpu_usage'].mean()
    plt.bar(cpu_by_hour.index, cpu_by_hour.values, color='skyblue')
    plt.title('Uso Promedio de CPU por Hora del Día')
    plt.xlabel('Hora')
    plt.ylabel('Uso Promedio de CPU (%)')
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('graficas/cpu_por_hora.png')
    plt.close()
    
    plt.figure(figsize=(12, 6))
    mem_by_hour = df.groupby('hour')['memory_mb'].mean()
    plt.bar(mem_by_hour.index, mem_by_hour.values, color='lightgreen')
    plt.title('Uso Promedio de Memoria por Hora del Día')
    plt.xlabel('Hora')
    plt.ylabel('Uso Promedio de Memoria (MB)')
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('graficas/memoria_por_hora.png')
    plt.close()
    
    plt.figure(figsize=(12, 6))
    net_by_hour = df.groupby('hour')['network_kb'].mean()
    plt.bar(net_by_hour.index, net_by_hour.values, color='salmon')
    plt.title('Tráfico Promedio de Red por Hora del Día')
    plt.xlabel('Hora')
    plt.ylabel('Tráfico de Red Promedio (KB)')
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('graficas/red_por_hora.png')
    plt.close()

def generar_reporte_analisis(df):
    """Genera un archivo de texto con el análisis de los datos"""
    total_samples = len(df)
    duration_hours = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
    
    avg_cpu = df['cpu_usage'].mean()
    max_cpu = df['cpu_usage'].max()
    min_cpu = df['cpu_usage'].min()
    max_cpu_idx = df['cpu_usage'].idxmax()
    max_cpu_timestamp = df.loc[max_cpu_idx, 'timestamp']
    max_cpu_process = df.loc[max_cpu_idx, 'top_process']
    
    avg_memory = df['memory_mb'].mean()
    max_memory = df['memory_mb'].max()
    min_memory = df['memory_mb'].min()
    
    avg_network = df['network_kb'].mean()
    max_network = df['network_kb'].max()
    total_network_mb = df['network_kb'].sum() / 1024 
    
    has_temp_data = df['temperature_c'].notna().sum() > 0
    if has_temp_data:
        temp_df = df[df['temperature_c'].notna()]
        avg_temp = temp_df['temperature_c'].mean()
        max_temp = temp_df['temperature_c'].max()
        min_temp = temp_df['temperature_c'].min()
    
    corr_cpu_mem = df['cpu_usage'].corr(df['memory_mb'])
    corr_cpu_net = df['cpu_usage'].corr(df['network_kb'])
    
    cpu_by_hour = df.groupby(df['timestamp'].dt.hour)['cpu_usage'].mean()
    peak_cpu_hour = cpu_by_hour.idxmax()
    net_by_hour = df.groupby(df['timestamp'].dt.hour)['network_kb'].mean()
    peak_net_hour = net_by_hour.idxmax()
    
    proceso_mas_frecuente = df.attrs.get('proceso_mas_frecuente', "No disponible")
    proceso_max_cpu = df.attrs.get('proceso_max_cpu', "No disponible")
    valor_max_cpu = df.attrs.get('valor_max_cpu', 0)
    timestamp_max_cpu = df.attrs.get('timestamp_max_cpu', None)
    top_procesos = df.attrs.get('top_5_procesos', [])
    
    # Generar informe
    with open('reporte_analisis.txt', 'w', encoding='utf-8') as f:
        f.write("===== REPORTE DE ANÁLISIS DE MÉTRICAS DE SISTEMA =====\n\n")
        f.write(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de muestras analizadas: {total_samples}\n")
        f.write(f"Duración del monitoreo: {duration_hours:.2f} horas\n\n")
        
        f.write("--- ANÁLISIS DE CPU ---\n")
        f.write(f"Promedio de uso de CPU: {avg_cpu:.2f}%\n")
        f.write(f"Máximo de uso de CPU: {max_cpu:.2f}%\n")
        f.write(f"Mínimo de uso de CPU: {min_cpu:.2f}%\n")
        f.write(f"El uso máximo de CPU ocurrió el {max_cpu_timestamp.strftime('%d/%m/%Y a las %H:%M:%S')}\n")
        f.write(f"Proceso activo durante el máximo uso de CPU: {max_cpu_process}\n\n")
        
        f.write("--- ANÁLISIS DE PROCESOS ---\n")
        f.write(f"Proceso más frecuente en la posición #1: {proceso_mas_frecuente}\n")
        f.write(f"Proceso con el pico más alto de CPU: {proceso_max_cpu} ({valor_max_cpu:.2f}%)\n")
        if timestamp_max_cpu:
            f.write(f"Fecha/hora del pico más alto: {timestamp_max_cpu.strftime('%d/%m/%Y a las %H:%M:%S')}\n\n")
        
        f.write("Top 5 procesos más frecuentes:\n")
        for i, (proceso, datos) in enumerate(top_procesos, 1):
            porcentaje = (datos['count'] / total_samples) * 100
            f.write(f"{i}. {proceso}: {porcentaje:.1f}% del tiempo ({datos['count']} muestras, pico: {datos['highest_cpu']:.2f}% CPU)\n")
        f.write("\n")
        
        f.write("--- ANÁLISIS DE MEMORIA ---\n")
        f.write(f"Promedio de uso de memoria: {avg_memory:.2f} MB\n")
        f.write(f"Máximo de uso de memoria: {max_memory:.2f} MB\n")
        f.write(f"Mínimo de uso de memoria: {min_memory:.2f} MB\n\n")
        
        f.write("--- ANÁLISIS DE RED ---\n")
        f.write(f"Promedio de tráfico de red: {avg_network:.2f} KB\n")
        f.write(f"Máximo de tráfico de red: {max_network:.2f} KB\n")
        f.write(f"Total de datos transferidos: {total_network_mb:.2f} MB\n\n")
        
        if has_temp_data:
            f.write("--- ANÁLISIS DE TEMPERATURA ---\n")
            f.write(f"Promedio de temperatura: {avg_temp:.2f}°C\n")
            f.write(f"Máxima temperatura: {max_temp:.2f}°C\n")
            f.write(f"Mínima temperatura: {min_temp:.2f}°C\n")
            if max_temp > 80:
                f.write("ALERTA: Se detectaron temperaturas superiores a 80°C\n")
            f.write("\n")
        
        f.write("--- ANÁLISIS DE CORRELACIONES ---\n")
        f.write(f"Correlación entre CPU y Memoria: {corr_cpu_mem:.2f}\n")
        if corr_cpu_mem > 0.7:
            f.write("Existe una fuerte correlación positiva entre el uso de CPU y memoria\n")
        elif corr_cpu_mem > 0.3:
            f.write("Existe una correlación moderada entre el uso de CPU y memoria\n")
        else:
            f.write("No existe una correlación significativa entre el uso de CPU y memoria\n")
        
        f.write(f"Correlación entre CPU y Red: {corr_cpu_net:.2f}\n")
        if corr_cpu_net > 0.7:
            f.write("Existe una fuerte correlación entre CPU y tráfico de red\n")
        elif corr_cpu_net > 0.3:
            f.write("Existe una correlación moderada entre CPU y red\n")
        else:
            f.write("El uso de red parece independiente del uso de CPU\n\n")
        
        f.write("--- PATRONES TEMPORALES ---\n")
        f.write(f"Hora con mayor uso de CPU: {peak_cpu_hour}:00 - {peak_cpu_hour}:59 ({cpu_by_hour[peak_cpu_hour]:.2f}%)\n")
        f.write(f"Hora con mayor tráfico de red: {peak_net_hour}:00 - {peak_net_hour}:59 ({net_by_hour[peak_net_hour]:.2f} KB)\n\n")
        
        f.write("--- CONCLUSIONES Y RECOMENDACIONES ---\n")
        if max_cpu > 80:
            f.write("⚠️ Se detectaron picos de CPU superiores al 80%, lo que puede causar lentitud en el sistema.\n")
            f.write("   Recomendación: Revisar los procesos que consumen más CPU.\n")
        
        if avg_memory > 8000:
            f.write("⚠️ El uso de memoria promedio es alto (más de 8 GB).\n")
            f.write("   Recomendación: Considerar aumentar la RAM del sistema o cerrar aplicaciones innecesarias.\n")
        
        f.write("\nEste reporte proporciona una visión general del rendimiento del sistema durante el período de monitoreo.\n")
        f.write("Para un análisis más detallado, revise las gráficas generadas en el directorio 'graficas'.\n")

if __name__ == "__main__":
    import sys
    
    # Si se proporciona un nombre de archivo como argumento, úsalo
    if len(sys.argv) > 1:
        archivo_csv = sys.argv[1]
        analizar_metricas(archivo_csv)
    else:
        # De lo contrario, usa el nombre de archivo predeterminado
        analizar_metricas()