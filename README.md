# Sistema Monitor

Un monitor de métricas de sistema desarrollado en Rust que recopila y analiza el rendimiento de tu computadora durante 48 horas continuas.

## Descripción

Este programa monitorea automáticamente las métricas clave de tu sistema operativo Windows, incluyendo uso de CPU, memoria, tráfico de red y temperatura del procesador. Los datos se recopilan cada 10 minutos durante un período de 48 horas y se almacenan en formato CSV para su posterior análisis.

## Funcionalidades

### Monitoreo en Tiempo Real
- **CPU**: Porcentaje de uso global y por núcleo, frecuencia de operación
- **Memoria**: Uso de RAM en MB y porcentaje de utilización
- **Procesos**: Identificación de los 5 procesos que más CPU consumen
- **Red**: Tráfico de datos enviados y recibidos en KB
- **Temperatura**: Lecturas del sensor térmico del procesador
- **Discos**: Estado y espacio disponible en unidades de almacenamiento
- **Conexiones**: Número de conexiones de red activas

### Análisis y Reportes
Después de las 48 horas, el programa genera automáticamente:
- **Gráficos PNG** con visualizaciones de uso de CPU, memoria y red
- **Análisis estadístico** con promedios, máximos y mínimos
- **Correlaciones** entre diferentes métricas del sistema
- **Patrones temporales** por horas del día
- **Proyecciones** de tendencias futuras
- **Recomendaciones** basadas en el análisis de datos

### Archivos Generados
- `metricas.csv`: Datos raw de todas las mediciones
- `cpu_usage.png`: Gráfico del uso de CPU a lo largo del tiempo
- `memory_usage.png`: Gráfico del consumo de memoria
- `network_traffic.png`: Gráfico del tráfico de red

## Requisitos del Sistema

### Sistema Operativo
- **Windows** (utiliza APIs específicas de Windows para obtener información del sistema)

### Dependencias de Rust
El proyecto utiliza las siguientes librerías de Rust:

```toml
[dependencies]
sysinfo = "0.29"        # Información del sistema
chrono = "0.4"          # Manejo de fechas y tiempo
plotters = "0.3"        # Generación de gráficos
csv = "1.1"             # Lectura/escritura de archivos CSV
windows = "0.44"        # APIs de Windows para WMI
winapi = "0.3"          # APIs de Windows adicionales
```

### Herramientas Requeridas
- **Rust** 1.70 o superior
- **Cargo** (incluido con Rust)
- **Compilador de C/C++** (MSVC Build Tools o Visual Studio)

## Instalación

### 1. Instalar Rust
Descarga e instala Rust desde [rustup.rs](https://rustup.rs/)

### 2. Instalar Build Tools
Instala Visual Studio Build Tools o Visual Studio Community con las herramientas de desarrollo de C++.

### 3. Clonar el Repositorio
```bash
git clone <url-del-repositorio>
cd monitor
```

### 4. Compilar el Proyecto
```bash
cargo build --release
```

## Uso

### Ejecutar el Monitor
```bash
cargo run --release
```

O ejecutar el binario compilado:
```bash
./target/release/monitor.exe
```

### Comportamiento del Programa
1. **Inicio**: Crea el archivo `metricas.csv` con los encabezados
2. **Monitoreo**: Recopila datos cada 10 minutos durante 48 horas
3. **Análisis**: Al completar las 48 horas, genera automáticamente los reportes
4. **Finalización**: El programa termina después de generar todos los archivos

### Configuración
Puedes modificar estos parámetros en el código fuente:

```rust
const ARCHIVO_DATOS: &str = "metricas.csv";  // Nombre del archivo de datos
const INTERVALO_MINUTOS: u64 = 10;           // Intervalo de captura en minutos
```

## Interpretación de Resultados

### Archivos CSV
El archivo `metricas.csv` contiene columnas para:
- `timestamp`: Fecha y hora de la medición
- `cpu_usage`: Porcentaje de uso de CPU
- `top_process`: Los 5 procesos que más CPU consumen
- `memory_mb`: Memoria utilizada en MB
- `temperature_c`: Temperatura del procesador en Celsius
- `network_kb`: Tráfico total de red en KB

### Análisis Automático
El programa proporciona análisis sobre:
- Correlaciones entre CPU, memoria y red
- Patrones de uso por hora del día
- Procesos que más frecuentemente consumen recursos
- Proyecciones de tendencias futuras
- Recomendaciones de optimización

## Limitaciones

- **Solo Windows**: Utiliza APIs específicas de Windows
- **Privilegios**: Algunas métricas requieren permisos de administrador
- **Sensores**: La temperatura puede no estar disponible en todos los sistemas
- **Duración fija**: El monitoreo está configurado para exactamente 48 horas

## Solución de Problemas

### Error de Compilación MSVC
Si encuentras errores de compilación, asegúrate de tener instalado Visual Studio Build Tools.

### Permisos Insuficientes
Ejecuta el programa como administrador si necesitas acceso completo a todas las métricas.

### Temperatura No Disponible
Si no se puede obtener la temperatura, el programa continuará funcionando sin esta métrica.

