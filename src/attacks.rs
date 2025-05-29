use std::fmt;
use std::time::{Duration, Instant};
use std::thread;
use std::sync::{Arc, Mutex, atomic::{AtomicBool, AtomicUsize, Ordering}};
use rand::{thread_rng, Rng};
use crate::logger::Logger;

const PACKET_SIZE_BYTES: f32 = 1500.0;
const MAX_MEMORY_PERCENTAGE: usize = 90;

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum AttackType {
    DDoS,
    CPUSpike,
    MemoryLeak,
}

impl fmt::Display for AttackType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AttackType::DDoS => write!(f, "DDoS"),
            AttackType::CPUSpike => write!(f, "CPU Spike"),
            AttackType::MemoryLeak => write!(f, "Memory Leak"),
        }
    }
}

pub trait Attack {
    fn start(&mut self);
    fn stop(&mut self);
    fn update_intensity(&mut self, intensity: f32);
    fn get_metrics(&self) -> (f32, String);
}

pub struct DDoSAttack {
    intensity: f32,
    running: Arc<AtomicBool>,
    threads: Vec<thread::JoinHandle<()>>,
    metrics: Arc<Mutex<(u32, f32)>>, 
    packet_count: Arc<AtomicUsize>,
    last_log: Arc<Mutex<std::time::Instant>>,
    logger: Arc<Mutex<Logger>>,
}

impl DDoSAttack {
    pub fn new(intensity: f32, logger: Arc<Mutex<Logger>>,) -> Self {
        Self {
            intensity,
            running: Arc::new(AtomicBool::new(false)),
            threads: Vec::new(),
            metrics: Arc::new(Mutex::new((0, 0.0))),
            packet_count: Arc::new(AtomicUsize::new(0)),
            last_log: Arc::new(Mutex::new(std::time::Instant::now())),
            logger,
        }
    }

    fn calculate_packets_per_second(&self) -> u32 {
        (self.intensity * 100.0) as u32
    }
}

impl Attack for DDoSAttack {
    fn start(&mut self) {
        self.running.store(true, Ordering::SeqCst);
        let running = self.running.clone();
        let packets_per_second = self.calculate_packets_per_second();
        let metrics = self.metrics.clone();
        let packet_count = self.packet_count.clone();
        let last_log = self.last_log.clone();
        
        packet_count.store(0, Ordering::SeqCst);
        if let Ok(mut last) = last_log.lock() {
            *last = Instant::now();
        }
        
        if let Ok(mut m) = metrics.lock() {
            *m = (packets_per_second, packets_per_second as f32 * PACKET_SIZE_BYTES / 1024.0 / 1024.0);
        }
        
        println!("🚀 Iniciando ataque DDoS simulado con intensidad {:.1}%", self.intensity);
        println!("📊 Velocidad objetivo: {} paquetes/seg ({:.2} MB/s)",
                packets_per_second,
                packets_per_second as f32 * PACKET_SIZE_BYTES / 1024.0 / 1024.0);
        
        let thread = thread::spawn(move || {
            let mut rng = thread_rng();
            let mut buffer = Vec::with_capacity(100);
            
            while running.load(Ordering::SeqCst) {
                let packets_per_batch = packets_per_second / 10;
                if packets_per_batch > 0 {
                    buffer.clear();
                    for _ in 0..packets_per_batch.min(100) {
                        let ip = format!("{}.{}.{}.{}",
                            rng.gen_range(1..255),
                            rng.gen_range(0..255),
                            rng.gen_range(0..255),
                            rng.gen_range(0..255)
                        );
                        buffer.push(ip);
                    }
                    
                    packet_count.fetch_add(buffer.len(), Ordering::SeqCst);
                    
                    let should_log = {
                        if let Ok(mut last) = last_log.lock() {
                            let now = Instant::now();
                            let elapsed = now.duration_since(*last);
                            if elapsed.as_secs() >= 1 {
                                *last = now;
                                true
                            } else {
                                false
                            }
                        } else {
                            false
                        }
                    };
                    
                    if should_log {
                        let count = packet_count.swap(0, Ordering::SeqCst);
                        println!("DDoS: Generados {} paquetes en el último segundo ({:.2} MB/s)", 
                            count, 
                            count as f32 * PACKET_SIZE_BYTES / 1024.0 / 1024.0);
                    }
                    
                    thread::sleep(Duration::from_millis(100));
                } else {
                    thread::sleep(Duration::from_millis(1000));
                }
            }
        });
        
        self.threads = vec![thread];
    }

    fn stop(&mut self) {
        self.running.store(false, Ordering::SeqCst);
        
        println!("Deteniendo ataque DDoS simulado");
        
        for thread in self.threads.drain(..) {
            if let Err(e) = thread.join() {
                eprintln!("Error joining DDoS attack thread: {:?}", e);
            }
        }
        
        println!("Ataque DDoS simulado detenido");
    }

    fn update_intensity(&mut self, intensity: f32) {
        let old_intensity = self.intensity;
        self.intensity = intensity;
        
        println!("Actualizando intensidad del DDoS: {:.1}% → {:.1}%", old_intensity, intensity);
        
        let packets_per_second = self.calculate_packets_per_second();
        if let Ok(mut m) = self.metrics.lock() {
            *m = (packets_per_second, packets_per_second as f32 * PACKET_SIZE_BYTES / 1024.0 / 1024.0);
        }
        
        println!("Nueva velocidad objetivo: {} paquetes/seg ({:.2} MB/s)",
                packets_per_second,
                packets_per_second as f32 * PACKET_SIZE_BYTES / 1024.0 / 1024.0);
        
        if (intensity - old_intensity).abs() > 10.0 && self.running.load(Ordering::SeqCst) {
            println!("Cambio significativo detectado, reiniciando simulación");
            self.stop();
            self.start();
        }
    }

    fn get_metrics(&self) -> (f32, String) {
        let (packets_per_second, bandwidth) = match self.metrics.lock() {
            Ok(m) => *m,
            Err(_) => (0, 0.0),
        };
        
        println!("📋 Métricas DDoS: {:.1}% intensidad, {} paquetes/seg, {:.2} MB/s",
               self.intensity, packets_per_second, bandwidth);
        
        (self.intensity, format!("{:.2} MB/s", bandwidth))
    }
}

pub struct CPUSpikeAttack {
    intensity: f32,
    running: Arc<AtomicBool>,
    threads: Vec<thread::JoinHandle<()>>,
    logger: Arc<Mutex<Logger>>,
}

impl CPUSpikeAttack {
    pub fn new(intensity: f32, logger: Arc<Mutex<Logger>>) -> Self {
        Self {
            intensity,
            running: Arc::new(AtomicBool::new(false)),
            threads: Vec::new(),
            logger,
        }
    }
}

impl Attack for CPUSpikeAttack {
    fn start(&mut self) {
        self.running.store(true, Ordering::SeqCst);
        let running = self.running.clone();
        
        let mut threads = Vec::new();
        
        let available_cpus = num_cpus::get();
        let thread_count = ((available_cpus as f32 * self.intensity / 100.0).max(1.0)) as usize;
        
        for _ in 0..thread_count {
            let running_clone = running.clone();
            let intensity = self.intensity;
            
            let thread = thread::spawn(move || {
                while running_clone.load(Ordering::SeqCst) {
                    let mut _sum = 0.0;
                    for i in 0..10000 {
                        _sum += (i as f64).sqrt();
                    }
                    
                    let work_time = (intensity / 100.0) * 10.0;
                    let sleep_time = 10.0 - work_time;
                    
                    if sleep_time > 0.0 {
                        thread::sleep(Duration::from_millis((sleep_time * 1000.0) as u64));
                    }
                }
            });
            
            threads.push(thread);
        }
        
        self.threads = threads;
    }

    fn stop(&mut self) {
        self.running.store(false, Ordering::SeqCst);
        
        for thread in self.threads.drain(..) {
            if let Err(e) = thread.join() {
                eprintln!("Error joining CPU spike thread: {:?}", e);
            }
        }
    }

    fn update_intensity(&mut self, intensity: f32) {
        let restart_needed = (intensity / 20.0).floor() != (self.intensity / 20.0).floor();
        
        self.intensity = intensity;
        
        if restart_needed && self.running.load(Ordering::SeqCst) {
            self.stop();
            self.start();
        }
    }

    fn get_metrics(&self) -> (f32, String) {
        (self.intensity, format!("{:.1}% CPU", self.intensity))
    }
}

pub struct MemoryLeakAttack {
    intensity: f32,
    running: Arc<AtomicBool>,
    memory_chunks: Arc<Mutex<Vec<Vec<u8>>>>,
    thread_handle: Option<thread::JoinHandle<()>>,
    logger: Arc<Mutex<Logger>>,
}

impl MemoryLeakAttack {
    pub fn new(intensity: f32, logger: Arc<Mutex<Logger>>) -> Self {
        Self {
            intensity,
            running: Arc::new(AtomicBool::new(false)),
            memory_chunks: Arc::new(Mutex::new(Vec::new())),
            thread_handle: None,
            logger,
        }
    }

    fn calculate_chunk_size(&self) -> usize {
        (self.intensity * 1024.0 * 1024.0 / 10.0) as usize 
    }
}

impl Attack for MemoryLeakAttack {
    fn start(&mut self) {
        self.running.store(true, Ordering::SeqCst);
        let running = self.running.clone();
        let memory_chunks = self.memory_chunks.clone();
        let chunk_size = self.calculate_chunk_size();
        let intensity = self.intensity;
        
        let thread = thread::spawn(move || {
            while running.load(Ordering::SeqCst) {
                let can_allocate = {
                    let chunks = match memory_chunks.lock() {
                        Ok(guard) => guard,
                        Err(_) => continue, 
                    };
                    
                    let total_allocated = chunks.len() * chunk_size;
                    
                    if let Ok(mem_info) = sys_info::mem_info() {
                        total_allocated < mem_info.total as usize * 1024 * MAX_MEMORY_PERCENTAGE / 100
                    } else {
                        false 
                    }
                };
                
                if can_allocate {
                    
                    if let Ok(mut chunks) = memory_chunks.lock() {
                        let mut new_chunk = Vec::with_capacity(chunk_size);
                        new_chunk.resize(chunk_size, 0u8);
                        chunks.push(new_chunk);
                    }
                } else {
                    println!("Memory allocation paused: reached safety threshold");
                }
                
                let sleep_ms = (1000.0 * (100.0 - intensity) / 100.0).max(100.0) as u64;
                thread::sleep(Duration::from_millis(sleep_ms));
            }
        });
        
        self.thread_handle = Some(thread);
    }

    fn stop(&mut self) {
        self.running.store(false, Ordering::SeqCst);
        
        if let Some(thread) = self.thread_handle.take() {
            if let Err(e) = thread.join() {
                eprintln!("Error joining memory leak thread: {:?}", e);
            }
        }
        
        if let Ok(mut chunks) = self.memory_chunks.lock() {
            chunks.clear();
        } else {
            eprintln!("Failed to clear memory chunks on stop");
        }
    }

    fn update_intensity(&mut self, intensity: f32) {
        self.intensity = intensity;
    }

    fn get_metrics(&self) -> (f32, String) {
        let total_allocated = match self.memory_chunks.lock() {
            Ok(chunks) => chunks.len() * self.calculate_chunk_size(),
            Err(_) => 0,
        };
        
        let mem_mb = total_allocated as f32 / 1024.0 / 1024.0;
        
        (self.intensity, format!("{:.2} MB", mem_mb))
    }
}

extern crate num_cpus;

extern crate sys_info;