use sysinfo::{System, SystemExt, NetworkExt, ProcessExt, CpuExt};
use chrono::{DateTime, Duration, Local};
use std::{fs::{self, OpenOptions}, io::Write, path::Path, thread, time::Duration as StdDuration};
use std::error::Error;
use std::collections::HashMap;
use plotters::prelude::*;
use csv::ReaderBuilder;
use chrono::Datelike;
use chrono::Timelike;
use windows::Win32::System::Wmi::IWbemLocator;
use windows::Win32::System::Com::{CoCreateInstance, CoInitializeEx, CLSCTX_INPROC_SERVER, COINIT_MULTITHREADED};
use windows::core::BSTR;
use windows::core::GUID;
use windows::Win32::System::Wmi::{WBEM_FLAG_FORWARD_ONLY, WBEM_FLAG_RETURN_IMMEDIATELY};
use windows::Win32::System::Wmi::IWbemClassObject;
use windows::Win32::System::Com::{VARIANT, VT_I4};
use windows::core::PCWSTR;
use std::process::Command;
use winapi::um::sysinfoapi::GetTickCount64;
use sysinfo::DiskExt;

const ARCHIVO_DATOS: &str = "metricas.csv";
const INTERVALO_MINUTOS: u64 = 10;
const CLSID_WBEMLOCATOR: GUID = GUID::from_u128(0x4590F811_1D3A_11D0_891F_00AA004B2E24);


#[derive(Debug)]
struct MetricEntry {
    timestamp: DateTime<Local>,
    cpu_usage: f32,
    top_process: String,
    memory_mb: u64,
    temperature_c: Option<f32>,
    network_kb: u64,
}

fn main() {
    println!("Iniciando monitor de métricas de sistema...");
    println!("Capturando datos cada {} minutos durante 48 horas", INTERVALO_MINUTOS);
    println!("Guardando datos en '{}'", ARCHIVO_DATOS);
    
    if !Path::new(ARCHIVO_DATOS).exists() {
        let header = "timestamp,cpu_usage,top_process,memory_mb,temperature_c,network_kb\n";
        let mut archivo = OpenOptions::new()
            .create(true)
            .write(true)
            .open(ARCHIVO_DATOS)
            .expect("No se pudo crear el archivo de datos");
        
        archivo.write_all(header.as_bytes()).unwrap();
        println!("Archivo de datos creado con éxito.");
    }
    
    let mut sistema = System::new_all();
    
    loop {
        sistema.refresh_all();
        guardar_datos(&sistema);

        if han_pasado_48_horas() {
            println!("Han pasado 48 horas. Generando reporte...");
            if let Err(e) = generar_reporte() {
                eprintln!("Error al generar el reporte: {}", e);
            }
            break;
        }

        println!("Esperando {} minutos para la próxima captura...", INTERVALO_MINUTOS);
        thread::sleep(StdDuration::from_secs(INTERVALO_MINUTOS * 60));
    }
}

fn obtener_temperatura_windows() -> Result<f32, Box<dyn Error>> {
    unsafe {
        CoInitializeEx(None, COINIT_MULTITHREADED)?;

        let locator: IWbemLocator = CoCreateInstance(&CLSID_WBEMLOCATOR, None, CLSCTX_INPROC_SERVER)?;

        let server = BSTR::from("ROOT\\CIMV2");  
        let services = locator.ConnectServer(
            &server,
            &BSTR::new(),  
            &BSTR::new(),  
            &BSTR::new(),  
            0,
            &BSTR::new(),  
            None,
        )?;

        let query = BSTR::from("SELECT * FROM Win32_TemperatureProbe");
        let enumerator = services.ExecQuery(
            &BSTR::from("WQL"),
            &query,
            WBEM_FLAG_FORWARD_ONLY | WBEM_FLAG_RETURN_IMMEDIATELY,
            None,
        )?;

        let mut temperature = None;
        
        let mut objs: [Option<IWbemClassObject>; 1] = [None];
        let mut returned = 0;

        loop {
            let hr = enumerator.Next(0, &mut objs, &mut returned);
            if hr.is_err() || returned == 0 {
                break;
            }

            if let Some(obj) = &objs[0] {
                let mut vt_value = VARIANT::default();
                let mut vt_type = 0;
                let mut vt_flavor = 0;

                let prop_name = "CurrentReading\0"; 
                let prop_wide: Vec<u16> = prop_name.encode_utf16().collect();

                {
                    obj.Get(
                        PCWSTR(prop_wide.as_ptr()),
                        0,
                        &mut vt_value,
                        &mut vt_type,
                        &mut vt_flavor,
                    )?;
                }

                if vt_value.Anonymous.Anonymous.vt == VT_I4 {
                    let raw_temp: i32 = { vt_value.Anonymous.Anonymous.Anonymous.lVal };
                    let celsius = (raw_temp as f32 - 2732.0) / 10.0;
                    temperature = Some(celsius);
                }

                break;
            }
        }

        temperature.ok_or_else(|| "No se pudo obtener temperatura".into())
    }
}

fn imprimir_info_disco(sistema: &System) {
    for disco in sistema.disks() {
        println!("  - Disco {:?}:", disco.name());
        println!("      Tipo: {:?}", disco.kind()); 
        println!("      Montado en: {:?}", disco.mount_point());
        println!("      Total: {} bytes", disco.total_space());
        println!("      Disponible: {} bytes", disco.available_space());
    }

    let ticks = unsafe { GetTickCount64() };
    println!("  - Tiempo desde encendido (ms): {}", ticks);
}

fn nombre_archivo_segun_fecha() -> String {
    let ahora = Local::now();
    format!("metricas{}.csv", ahora.format("%Y%m%d"))
}

fn guardar_datos(sistema: &System) {
    let ahora = Local::now();
    println!("[{}] Capturando métricas...", ahora);
    
    let cpu = sistema.global_cpu_info().cpu_usage();
    println!("  - CPU global: {:.2}%", cpu);

    for (i, cpu) in sistema.cpus().iter().enumerate() {
        println!("  - CPU {}: {:.2}% @ {} MHz", i, cpu.cpu_usage(), cpu.frequency());
    }

    let mut procesos: Vec<(f32, String)> = sistema.processes().iter()
    .map(|(pid, proc)| (proc.cpu_usage(), format!("{} (PID: {})", proc.name(), pid)))
    .collect();

    procesos.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    let top_5: Vec<String> = procesos.iter().take(5)
        .map(|(uso, nombre)| format!("{}: {:.2}%", nombre, uso))
        .collect();

    let top_5_str = format!("\"{}\"", top_5.join("\n"));

    
    let memoria = sistema.used_memory();
    let total_mem = sistema.total_memory();
    println!("  - Memoria usada: {} MB / {} MB ({:.2}%)", 
        memoria / (1024 * 1024), 
        total_mem / (1024 * 1024),
        (memoria as f32 / total_mem as f32) * 100.0);
    
    let temperature = match obtener_temperatura_windows() {
        Ok(t) => Some(t),
        Err(e) => {
            eprintln!("Error al obtener temperatura: {}", e);
            None
        }
    };

    let mut red_total: u64 = 0;
    for (nombre, interfaz) in sistema.networks() {
        let recibido = interfaz.received();
        let enviado = interfaz.transmitted();
        println!("  - Red {}: Recibido {} KB, Enviado {} KB", 
            nombre, recibido / 1024, enviado / 1024);
        red_total += recibido + enviado;
    }
    println!("  - Red total: {} KB", red_total / 1024);

    obtener_conexiones_activas();
    imprimir_info_disco(sistema);


    let mut max_cpu = 0.0;
    let mut proceso_top = "N/A".to_string();
    
    for (pid, process) in sistema.processes() {
        let cpu_usage = process.cpu_usage();
        if cpu_usage > max_cpu {
            max_cpu = cpu_usage;
            proceso_top = format!("{} (PID: {}, {:.2}%)", process.name(), pid, cpu_usage);
        }
    }
    println!("  - Proceso con mayor uso de CPU: {}", proceso_top);

    let temp_str = temperature.map(|t| t.to_string()).unwrap_or_default();
    let linea = format!("{},{:.2},{},{}MB,{},{}KB\n", 
        ahora.to_rfc3339(), 
        cpu,               
        top_5_str,        
        memoria / (1024 * 1024), 
        temp_str,
        red_total / 1024  
    );

    let _nombre_archivo = nombre_archivo_segun_fecha();
    let mut archivo = OpenOptions::new()
        .create(true)
        .append(true)
        .open(ARCHIVO_DATOS)
        .expect("No se pudo abrir el archivo de datos");

    archivo.write_all(linea.as_bytes()).unwrap();
    println!("[{}] Datos guardados en '{}'.", ahora, ARCHIVO_DATOS);
}

fn obtener_conexiones_activas() {
    let output = Command::new("netstat")
        .arg("-n")
        .output()
        .expect("Fallo al ejecutar netstat");

    let salida = String::from_utf8_lossy(&output.stdout);
    let count = salida.lines()
        .filter(|line| line.starts_with("  TCP") || line.starts_with("  UDP"))
        .count();

    println!("  - Conexiones activas: {}", count);
}

fn han_pasado_48_horas() -> bool {
    if !Path::new(ARCHIVO_DATOS).exists() {
        return false;
    }

    let contenido = match fs::read_to_string(ARCHIVO_DATOS) {
        Ok(content) => content,
        Err(_) => return false,
    };
    
    let lineas: Vec<&str> = contenido.lines().collect();
    
    if lineas.len() <= 1 {
        return false;
    }
    
    let primera_linea = lineas[1]; 
    
    if let Some(fecha_str) = primera_linea.split(',').next() {
        match DateTime::parse_from_rfc3339(fecha_str) {
            Ok(fecha_inicio) => {
                let fecha_inicio_local = fecha_inicio.with_timezone(&Local);
                let ahora = Local::now();
                
                let duracion = ahora.signed_duration_since(fecha_inicio_local);
                
                println!("Tiempo transcurrido desde la primera captura: {} horas", 
                         duracion.num_minutes() as f64 / 60.0);
                
                return duracion >= Duration::hours(48);
            },
            Err(e) => {
                eprintln!("Error parsing date from CSV: {}", e);
                return false;
            }
        }
    }
    false
}

fn parse_temperature(s: &str) -> Option<f32> {
    if s == "None" {
        None
    } else {
        s.parse().ok()
    }
}

fn generar_reporte() -> Result<(), Box<dyn Error>> {
    println!("Generando reporte de análisis de métricas...");
    
    let mut entries: Vec<MetricEntry> = Vec::new();
    let mut rdr = ReaderBuilder::new().has_headers(true).from_path(ARCHIVO_DATOS)?;
    
    for result in rdr.records() {
        let record = result?;
        if record.len() >= 5 {
            let timestamp = DateTime::parse_from_rfc3339(&record[0])
                .map(|dt| dt.with_timezone(&Local))?;
                
            let cpu_usage = record[1].trim().parse::<f32>()?;
            let top_process = record[2].trim_matches('"').replace("\n", "; "); 
            let memory_mb = record[3].trim().replace("MB", "").parse::<u64>()?;
            let temperature_str = record[4].trim(); 
            let temperature_c = parse_temperature(temperature_str); 
            let network_kb = record[5].trim().replace("KB", "").parse::<u64>()?;       
            entries.push(MetricEntry {
                timestamp,
                cpu_usage,
                top_process,
                memory_mb,
                temperature_c,
                network_kb,
            });
        }
    }
    
    if entries.is_empty() {
        println!("No hay datos suficientes para generar el reporte.");
        return Ok(());
    }
    
    crear_grafica_cpu(&entries)?;
    
    crear_grafica_memoria(&entries)?;
    
    crear_grafica_red(&entries)?;
    
    analizar_datos(&entries);
    
    println!("Reporte generado con éxito. Revisa los archivos 'cpu_usage.png', 'memory_usage.png', y 'network_traffic.png'");
    Ok(())
}

fn crear_grafica_cpu(entries: &[MetricEntry]) -> Result<(), Box<dyn Error>> {
    let root = BitMapBackend::new("cpu_usage.png", (800, 600)).into_drawing_area();
    root.fill(&WHITE)?;
    
    let min_time = entries.first().unwrap().timestamp;
    let max_time = entries.last().unwrap().timestamp;
    
    let mut chart = ChartBuilder::on(&root)
        .caption("Uso de CPU durante 48 horas", ("sans-serif", 30).into_font())
        .margin(5)
        .x_label_area_size(40)
        .y_label_area_size(40)
        .build_cartesian_2d(min_time..max_time, 0f32..100f32)?;
    
    chart.configure_mesh()
        .x_labels(20)
        .y_labels(10)
        .x_label_formatter(&|x| x.format("%d/%m %H:%M").to_string())
        .y_label_formatter(&|y| format!("{:.1}%", y))
        .draw()?;
    
    chart.draw_series(LineSeries::new(
        entries.iter().map(|e| (e.timestamp, e.cpu_usage)),
        &RED,
    ))?;
    
    let max_entry = entries.iter().max_by(|a, b| a.cpu_usage.partial_cmp(&b.cpu_usage).unwrap()).unwrap();
    chart.draw_series(PointSeries::of_element(
        vec![(max_entry.timestamp, max_entry.cpu_usage)],
        5,
        ShapeStyle::from(&RED).filled(),
        &|coord, size, style| {
            EmptyElement::at(coord)
                + Circle::new((0, 0), size, style)
                + Text::new(format!("Máximo: {:.2}%", max_entry.cpu_usage), (10, 0), ("sans-serif", 15).into_font())
        },
    ))?;
    
    root.present()?;
    Ok(())
}

fn crear_grafica_memoria(entries: &[MetricEntry]) -> Result<(), Box<dyn Error>> {
    let root = BitMapBackend::new("memory_usage.png", (800, 600)).into_drawing_area();
    root.fill(&WHITE)?;
    
    let min_time = entries.first().unwrap().timestamp;
    let max_time = entries.last().unwrap().timestamp;
    let max_memory = entries.iter().map(|e| e.memory_mb).max().unwrap() * 12 / 10; 
    
    let mut chart = ChartBuilder::on(&root)
        .caption("Uso de Memoria durante 48 horas", ("sans-serif", 30).into_font())
        .margin(5)
        .x_label_area_size(40)
        .y_label_area_size(60)
        .build_cartesian_2d(min_time..max_time, 0u64..max_memory)?;
    
    chart.configure_mesh()
        .x_labels(20)
        .y_labels(10)
        .x_label_formatter(&|x| x.format("%d/%m %H:%M").to_string())
        .y_label_formatter(&|y| format!("{}MB", y))
        .draw()?;
    
    chart.draw_series(LineSeries::new(
        entries.iter().map(|e| (e.timestamp, e.memory_mb)),
        &BLUE,
    ))?;
    
    let avg_memory = entries.iter().map(|e| e.memory_mb).sum::<u64>() / entries.len() as u64;
    chart.draw_series(LineSeries::new(
        vec![(min_time, avg_memory), (max_time, avg_memory)],
        &GREEN.mix(0.5),
    ))?
    .label(format!("Promedio: {}MB", avg_memory))
    .legend(|(x, y)| PathElement::new(vec![(x, y), (x + 20, y)], &GREEN));
    
    chart.configure_series_labels()
        .background_style(&WHITE.mix(0.8))
        .border_style(&BLACK)
        .draw()?;
    
    root.present()?;
    Ok(())
}

fn crear_grafica_red(entries: &[MetricEntry]) -> Result<(), Box<dyn Error>> {
    let root = BitMapBackend::new("network_traffic.png", (800, 600)).into_drawing_area();
    root.fill(&WHITE)?;
    
    let min_time = entries.first().unwrap().timestamp;
    let max_time = entries.last().unwrap().timestamp;
    let max_network = entries.iter().map(|e| e.network_kb).max().unwrap() * 12 / 10; // 120% of max
    
    let mut chart = ChartBuilder::on(&root)
        .caption("Tráfico de Red durante 48 horas", ("sans-serif", 30).into_font())
        .margin(5)
        .x_label_area_size(40)
        .y_label_area_size(60)
        .build_cartesian_2d(min_time..max_time, 0u64..max_network)?;
    
    chart.configure_mesh()
        .x_labels(20)
        .y_labels(10)
        .x_label_formatter(&|x| x.format("%d/%m %H:%M").to_string())
        .y_label_formatter(&|y| format!("{}KB", y))
        .draw()?;
    
    chart.draw_series(LineSeries::new(
        entries.iter().map(|e| (e.timestamp, e.network_kb)),
        &MAGENTA,
    ))?;
    
    root.present()?;
    Ok(())
}

fn analizar_datos(entries: &[MetricEntry]) {
    println!("\n===== ANÁLISIS DE DATOS =====");
    
    let num_entries = entries.len();
    println!("Total de muestras recolectadas: {}", num_entries);
    
    let avg_cpu = entries.iter().map(|e| e.cpu_usage).sum::<f32>() / num_entries as f32;
    let max_cpu = entries.iter().map(|e| e.cpu_usage).fold(0.0, f32::max);
    let min_cpu = entries.iter().map(|e| e.cpu_usage).fold(100.0, f32::min);
    
    println!("\n--- Análisis de CPU ---");
    println!("Promedio de uso de CPU: {:.2}%", avg_cpu);
    println!("Máximo de uso de CPU: {:.2}%", max_cpu);
    println!("Mínimo de uso de CPU: {:.2}%", min_cpu);
    
    let max_cpu_entry = entries.iter()
        .max_by(|a, b| a.cpu_usage.partial_cmp(&b.cpu_usage).unwrap())
        .unwrap();
    println!("El uso máximo de CPU ocurrió el {} con un valor de {:.2}% durante la ejecución de {}",
        max_cpu_entry.timestamp.format("%d/%m/%Y a las %H:%M:%S"),
        max_cpu_entry.cpu_usage,
        max_cpu_entry.top_process);
    
    let avg_memory = entries.iter().map(|e| e.memory_mb).sum::<u64>() / num_entries as u64;
    let max_memory = entries.iter().map(|e| e.memory_mb).max().unwrap();
    
    println!("\n--- Análisis de Memoria ---");
    println!("Promedio de uso de memoria: {}MB", avg_memory);
    println!("Máximo de uso de memoria: {}MB", max_memory);
    
    let avg_network = entries.iter().map(|e| e.network_kb).sum::<u64>() / num_entries as u64;
    let max_network = entries.iter().map(|e| e.network_kb).max().unwrap();
    
    println!("\n--- Análisis de Red ---");
    println!("Promedio de tráfico de red: {}KB", avg_network);
    println!("Máximo de tráfico de red: {}KB", max_network);
    
    let mut process_frequency: HashMap<String, u32> = HashMap::new();
    for entry in entries {
        let process_name = entry.top_process.split(' ').next().unwrap_or("unknown").to_string();
        *process_frequency.entry(process_name).or_insert(0) += 1;
    }
    
    println!("\n--- Análisis de Procesos ---");
    println!("Procesos que más frecuentemente consumen más CPU:");
    let mut processes: Vec<(String, u32)> = process_frequency.into_iter().collect();
    processes.sort_by(|a, b| b.1.cmp(&a.1));
    
    for (i, (process, count)) in processes.iter().take(5).enumerate() {
        println!("{}. {} - {} apariciones ({:.1}% del tiempo)",
            i+1, process, count, (*count as f32 / num_entries as f32) * 100.0);
    }
    let procesos_en_picos = entries.iter()
        .filter(|e| e.cpu_usage > avg_cpu * 1.5)  
        .map(|e| e.top_process.clone())
        .collect::<Vec<_>>();
    println!("\n--- Procesos durante picos de CPU ---");
    if !procesos_en_picos.is_empty() {
        let mut contador_procesos: HashMap<String, u32> = HashMap::new();
        for proceso in procesos_en_picos {
            let nombre = proceso.split(' ').next().unwrap_or("unknown").to_string();
            *contador_procesos.entry(nombre).or_insert(0) += 1;
        }
        
        let mut proc_picos: Vec<(String, u32)> = contador_procesos.into_iter().collect();
        proc_picos.sort_by(|a, b| b.1.cmp(&a.1));
        
        for (i, (proceso, contador)) in proc_picos.iter().take(3).enumerate() {
            println!("{}. {} - presente en {} picos de CPU", 
                i+1, proceso, contador);
        }
        
        for proceso in &proc_picos {
            if proceso.0.to_lowercase().contains("chrome") || 
            proceso.0.to_lowercase().contains("firefox") || 
            proceso.0.to_lowercase().contains("edge") {
                println!("La CPU suele subir cuando se usa {}", proceso.0);
            }
        }
    }
    println!("\n--- Análisis de Correlaciones ---");
    
    let cpu_memory_correlation = calcular_correlacion(
        entries.iter().map(|e| e.cpu_usage as f64).collect::<Vec<f64>>(),
        entries.iter().map(|e| e.memory_mb as f64).collect::<Vec<f64>>()
    );
    
    println!("Correlación entre CPU y Memoria: {:.2}", cpu_memory_correlation);
    if cpu_memory_correlation > 0.7 {
        println!("Existe una fuerte correlación positiva entre el uso de CPU y memoria, lo que sugiere que las aplicaciones en uso son intensivas en ambos recursos.");
    } else if cpu_memory_correlation > 0.3 {
        println!("Existe una correlación moderada entre el uso de CPU y memoria.");
    } else {
        println!("No existe una correlación significativa entre el uso de CPU y memoria.");
    }
    
    let cpu_network_correlation = calcular_correlacion(
        entries.iter().map(|e| e.cpu_usage as f64).collect::<Vec<f64>>(),
        entries.iter().map(|e| e.network_kb as f64).collect::<Vec<f64>>()
    );
    
    println!("Correlación entre CPU y Red: {:.2}", cpu_network_correlation);
    if cpu_network_correlation > 0.7 {
        println!("Existe una fuerte correlación entre CPU y tráfico de red, lo que sugiere actividades intensivas en red que también consumen CPU (ej: descarga/subida de archivos, streaming).");
    } else if cpu_network_correlation > 0.3 {
        println!("Existe una correlación moderada entre CPU y red.");
    } else {
        println!("El uso de red parece independiente del uso de CPU.");
    }
    
    println!("\n--- Patrones Temporales ---");
    analizar_patrones_temporales(entries);
    
 
    println!("\n--- Proyecciones ---");
    if entries.len() > 24 {
        let memory_trend = calcular_tendencia(
            (0..entries.len()).map(|i| i as f64).collect::<Vec<f64>>(),
            entries.iter().map(|e| e.memory_mb as f64).collect::<Vec<f64>>()
        );
        
        if memory_trend.0 > 0.0 {
            println!("La memoria está incrementando a un ritmo de aproximadamente {:.2} MB por hora", memory_trend.0 * 6.0);

            let system_ram = 16384;
            let current_memory = entries.last().unwrap().memory_mb;
            
            if current_memory < system_ram && memory_trend.0 > 0.0 {
                let hours_until_full = ((system_ram - current_memory) as f64 / (memory_trend.0 * 6.0)).floor();
                if hours_until_full > 0.0 && hours_until_full < 10000.0 { 
                    println!("Si esta tendencia continúa, la memoria se agotará en aproximadamente {:.1} horas", hours_until_full);
                }
            }
        } else if memory_trend.0 < 0.0 {
            println!("El uso de memoria está disminuyendo a un ritmo de aproximadamente {:.2} MB por hora", -memory_trend.0 * 6.0);
        } else {
            println!("El uso de memoria se mantiene estable.");
        }
    }
    
    println!("\n--- Conclusión y Recomendaciones ---");
    if max_cpu > 80.0 {
        println!("Se detectaron picos de CPU superiores al 80%, lo que puede causar lentitud en el sistema.");
        println!("   Recomendación: Revisar los procesos '{}' que consumen más CPU.", 
                processes.first().map_or("N/A", |(name, _)| name));
    }
    
    if avg_memory > 8000 { 
        println!("El uso de memoria promedio es alto ({}MB).", avg_memory);
        println!("Recomendación: Considerar aumentar la RAM del sistema o cerrar aplicaciones innecesarias.");
    }
    

    let temps: Vec<f32> = entries.iter().filter_map(|e| e.temperature_c).collect();
    if !temps.is_empty() {
        let avg_temp = temps.iter().sum::<f32>() / temps.len() as f32;
        let max_temp = temps.iter().fold(0.0f32, |a: f32, &b| a.max(b));

        println!("\n--- Análisis de Temperatura ---");
        println!("Temperatura máxima: {:.1}°C", max_temp);
        println!("Temperatura promedio: {:.1}°C", avg_temp);

        if max_temp > 85.0 {
            println!("ALERTA: Temperatura crítica detectada (>85°C)");
        }
    }

    println!("\nAnálisis completo. Este reporte proporciona una visión general del rendimiento del sistema durante las últimas 48 horas.");
}

fn calcular_correlacion(x: Vec<f64>, y: Vec<f64>) -> f64 {
    let n = x.len() as f64;
    
    let sum_x: f64 = x.iter().sum();
    let sum_y: f64 = y.iter().sum();
    
    let sum_x_squared: f64 = x.iter().map(|val| val * val).sum();
    let sum_y_squared: f64 = y.iter().map(|val| val * val).sum();
    
    let sum_xy: f64 = x.iter().zip(y.iter()).map(|(a, b)| a * b).sum();
    
    let numerator = n * sum_xy - sum_x * sum_y;
    let denominator = ((n * sum_x_squared - sum_x * sum_x) * (n * sum_y_squared - sum_y * sum_y)).sqrt();
    
    if denominator == 0.0 {
        0.0
    } else {
        numerator / denominator
    }
}

fn calcular_tendencia(x: Vec<f64>, y: Vec<f64>) -> (f64, f64) { // (slope, intercept)
    let n = x.len() as f64;
    
    let sum_x: f64 = x.iter().sum();
    let sum_y: f64 = y.iter().sum();
    
    let sum_x_squared: f64 = x.iter().map(|val| val * val).sum();
    let sum_xy: f64 = x.iter().zip(y.iter()).map(|(a, b)| a * b).sum();
    
    let slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x * sum_x);
    let intercept = (sum_y - slope * sum_x) / n;
    
    (slope, intercept)
}

fn analizar_patrones_temporales(entries: &[MetricEntry]) {
    let mut hours_cpu: HashMap<u32, Vec<f32>> = HashMap::new();
    let mut hours_memory: HashMap<u32, Vec<u64>> = HashMap::new();
    let mut hours_network: HashMap<u32, Vec<u64>> = HashMap::new();
    
    for entry in entries {
        let hour = entry.timestamp.hour();
        hours_cpu.entry(hour).or_insert_with(Vec::new).push(entry.cpu_usage);
        hours_memory.entry(hour).or_insert_with(Vec::new).push(entry.memory_mb);
        hours_network.entry(hour).or_insert_with(Vec::new).push(entry.network_kb);
    }
    
    let mut hour_avg_cpu: Vec<(u32, f32)> = hours_cpu.iter()
        .map(|(&hour, values)| (hour, values.iter().sum::<f32>() / values.len() as f32))
        .collect();
    hour_avg_cpu.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    
    let mut hour_avg_network: Vec<(u32, u64)> = hours_network.iter()
        .map(|(&hour, values)| (hour, values.iter().sum::<u64>() / values.len() as u64))
        .collect();
    hour_avg_network.sort_by(|a, b| b.1.cmp(&a.1));
    
    println!("Horas de mayor uso de CPU:");
    for (i, (hour, avg)) in hour_avg_cpu.iter().take(3).enumerate() {
        println!("{}. {:02}:00 - {:02}:59: {:.2}%", i+1, hour, hour, avg);
    }
    
    println!("Horas de mayor tráfico de red:");
    for (i, (hour, avg)) in hour_avg_network.iter().take(3).enumerate() {
        println!("{}. {:02}:00 - {:02}:59: {}KB", i+1, hour, hour, avg);
    }
    
    if entries.len() > 24 * 2 { 
        let mut weekday_network: HashMap<u32, Vec<u64>> = HashMap::new();
        
        for entry in entries {
            let weekday = entry.timestamp.weekday().num_days_from_monday();
            weekday_network.entry(weekday).or_insert_with(Vec::new).push(entry.network_kb);
        }
        
        if weekday_network.len() > 1 {
            let mut day_avg_network: Vec<(u32, u64)> = weekday_network.iter()
                .map(|(&day, values)| (day, values.iter().sum::<u64>() / values.len() as u64))
                .collect();
            day_avg_network.sort_by(|a, b| b.1.cmp(&a.1));
            
            let weekday_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
            
            println!("Días de mayor tráfico de red:");
            for (i, (day, avg)) in day_avg_network.iter().take(weekday_network.len()).enumerate() {
                println!("{}. {}: {}KB", i+1, weekday_names[*day as usize], avg);
            }
        }
    }
}