use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use serde::{Serialize, Deserialize};

mod attacks;
mod gui;
mod logger;
mod communication;

use attacks::{AttackType, Attack, DDoSAttack, CPUSpikeAttack, MemoryLeakAttack};
use communication::CommunicationManager;
use logger::Logger;
use eframe::egui;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct AttackMetrics {
    pub cpu_usage: f32,
    pub memory_usage: f32,
    pub network_traffic: f32,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct AttackConfig {
    pub enabled: bool,
    pub intensity: f32,
}

#[derive(Clone)]
pub struct AppState {
    pub attack_configs: HashMap<AttackType, AttackConfig>,
    pub active_attacks: HashMap<AttackType, Arc<Mutex<Box<dyn Attack + Send>>>>,
    pub attack_metrics: AttackMetrics,
    pub logger: Arc<Mutex<Logger>>,
    pub comm_manager: Arc<Mutex<CommunicationManager>>,
}

impl Default for AppState {
    fn default() -> Self {
        let mut attack_configs = HashMap::new();
        attack_configs.insert(AttackType::DDoS, AttackConfig { enabled: false, intensity: 50.0 });
        attack_configs.insert(AttackType::CPUSpike, AttackConfig { enabled: false, intensity: 50.0 });
        attack_configs.insert(AttackType::MemoryLeak, AttackConfig { enabled: false, intensity: 50.0 });

        Self {
            attack_configs,
            active_attacks: HashMap::new(),
            attack_metrics: AttackMetrics {
                cpu_usage: 0.0,
                memory_usage: 0.0,
                network_traffic: 0.0,
            },
            logger: Arc::new(Mutex::new(Logger::new())),
            comm_manager: Arc::new(Mutex::new(CommunicationManager::new())),
        }
    }
}

impl AppState {
    pub fn toggle_attack(&mut self, attack_type: AttackType) {
        let is_enabled = {
            let config = self.attack_configs.get_mut(&attack_type).unwrap();
            config.enabled = !config.enabled;
            config.enabled
        };
        
        let intensity = self.attack_configs.get(&attack_type).unwrap().intensity;

        if is_enabled {
            let logger = self.logger.clone();
            let attack: Box<dyn Attack + Send> = match attack_type {
                AttackType::DDoS => Box::new(DDoSAttack::new(intensity, self.logger.clone())),
                AttackType::CPUSpike => Box::new(CPUSpikeAttack::new(intensity, self.logger.clone())),
                AttackType::MemoryLeak => Box::new(MemoryLeakAttack::new(intensity, self.logger.clone())),
            };
            
            let attack_arc = Arc::new(Mutex::new(attack));
            self.active_attacks.insert(attack_type.clone(), attack_arc.clone());
            
            let logger = self.logger.clone();
            let mut logger = logger.lock().unwrap();
            logger.log(format!("Started {} attack with intensity {:.1}%", attack_type, intensity));
            
            let attack_type_clone = attack_type.clone();
            let attack_clone = attack_arc.clone();
            let comm_manager = self.comm_manager.clone();
            
            let attack_metrics = AttackMetrics {
                cpu_usage: if attack_type_clone == AttackType::CPUSpike { intensity } else { 0.0 },
                memory_usage: if attack_type_clone == AttackType::MemoryLeak { intensity } else { 0.0 },
                network_traffic: if attack_type_clone == AttackType::DDoS { intensity } else { 0.0 },
            };
            
            std::thread::spawn(move || {
                let mut attack = attack_clone.lock().unwrap(); 
                attack.start();
                
                let comm = comm_manager.lock().unwrap();
                comm.send_metrics(&attack_metrics);
            });
        } else {
            if let Some(attack_arc) = self.active_attacks.remove(&attack_type) {
                let mut attack = attack_arc.lock().unwrap(); 
                attack.stop();
                
                let logger = self.logger.clone();
                let mut logger = logger.lock().unwrap();
                logger.log(format!("Stopped {} attack", attack_type));
            }
        }
    }

    pub fn update_attack_intensity(&mut self, attack_type: AttackType, intensity: f32) {
        if let Some(config) = self.attack_configs.get_mut(&attack_type) {
            config.intensity = intensity;
            
            if config.enabled {
                if let Some(attack_arc) = self.active_attacks.get(&attack_type) {
                    let mut attack = attack_arc.lock().unwrap();
                    attack.update_intensity(intensity);
                    
                    let logger = self.logger.clone();
                    let mut logger = logger.lock().unwrap();
                    logger.log(format!("Updated {} attack intensity to {:.1}%", attack_type, intensity));
                }
            }
        }
    }
}

fn main() -> Result<(), eframe::Error> {
    env_logger::init();
    let options = eframe::NativeOptions {
        initial_window_size: Some(egui::vec2(1024.0, 768.0)),
        ..Default::default()
    };
    eframe::run_native(
        "Cyber Attack Simulator",
        options,
        Box::new(|_cc| Box::new(gui::CyberAttackApp::default())),
    )
}