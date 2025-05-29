use eframe::egui;
use crate::{AppState, attacks::AttackType};
use crate::communication::Protocol;

pub struct CyberAttackApp {
    app_state: AppState,
    selected_tab: Tab,
}

#[derive(PartialEq)]
enum Tab {
    Dashboard,
    Attacks,
    Logs,
    Settings,
}

impl Default for CyberAttackApp {
    fn default() -> Self {
        let app_state = AppState::default();
        let comm_manager = app_state.comm_manager.clone();
        let mut comm_manager = comm_manager.lock().unwrap();
        let _ = comm_manager.start();
        
        Self {
            app_state,
            selected_tab: Tab::Dashboard,
        }
    }
}

impl eframe::App for CyberAttackApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::TopBottomPanel::top("menu_bar").show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.heading("Cyber Attack Simulator");
                ui.separator();
                
                if ui.selectable_label(self.selected_tab == Tab::Dashboard, "Dashboard").clicked() {
                    self.selected_tab = Tab::Dashboard;
                }
                if ui.selectable_label(self.selected_tab == Tab::Attacks, "Attacks").clicked() {
                    self.selected_tab = Tab::Attacks;
                }
                if ui.selectable_label(self.selected_tab == Tab::Logs, "Logs").clicked() {
                    self.selected_tab = Tab::Logs;
                }
                if ui.selectable_label(self.selected_tab == Tab::Settings, "Settings").clicked() {
                    self.selected_tab = Tab::Settings;
                }
            });
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            match self.selected_tab {
                Tab::Dashboard => self.render_dashboard(ui),
                Tab::Attacks => self.render_attacks(ui),
                Tab::Logs => self.render_logs(ui),
                Tab::Settings => self.render_settings(ui),
            }
        });

        ctx.request_repaint_after(std::time::Duration::from_millis(500));
    }
}

impl CyberAttackApp {
    fn render_dashboard(&mut self, ui: &mut egui::Ui) {
        ui.heading("Attack Dashboard");
        ui.add_space(10.0);
        

        ui.horizontal(|ui| {
            ui.vertical(|ui| {
                ui.heading("Active Attacks");
                let active_count = self.app_state.attack_configs.values()
                    .filter(|config| config.enabled)
                    .count();
                ui.label(format!("{}", active_count));
            });
            
            ui.add_space(20.0);
            
            ui.vertical(|ui| {
                ui.heading("Network Traffic");
                let ddos_config = self.app_state.attack_configs.get(&AttackType::DDoS).unwrap();
                if ddos_config.enabled {
                    let packets = (ddos_config.intensity * 100.0) as u32;
                    ui.label(format!("{} packets/s", packets));
                } else {
                    ui.label("0 packets/s");
                }
            });
            
            ui.add_space(20.0);
            
            ui.vertical(|ui| {
                ui.heading("CPU Usage");
                let cpu_config = self.app_state.attack_configs.get(&AttackType::CPUSpike).unwrap();
                if cpu_config.enabled {
                    ui.label(format!("{:.1}%", cpu_config.intensity));
                } else {
                    ui.label("0.0%");
                }
            });
            
            ui.add_space(20.0);
            
            ui.vertical(|ui| {
                ui.heading("Memory Usage");
                let mem_config = self.app_state.attack_configs.get(&AttackType::MemoryLeak).unwrap();
                if mem_config.enabled {
                    let approximate_mb = (mem_config.intensity * 10.0) as u32;
                    ui.label(format!("~{} MB allocated", approximate_mb));
                } else {
                    ui.label("0 MB allocated");
                }
            });
        });
        
        ui.add_space(20.0);
        
        ui.heading("Quick Control Panel");
        ui.add_space(10.0);
        
        egui::Grid::new("dashboard_controls").striped(true).show(ui, |ui| {
            ui.label("Attack Type");
            ui.label("Status");
            ui.label("Intensity");
            ui.label("Action");
            ui.end_row();
            
            let attack_types = [AttackType::DDoS, AttackType::CPUSpike, AttackType::MemoryLeak];
            
            for attack_type in &attack_types {

                let attack_type_clone = attack_type.clone();
                let config = self.app_state.attack_configs.get(&attack_type).unwrap();
                let enabled = config.enabled;
                let current_intensity = config.intensity;
                
                ui.label(format!("{}", attack_type));
                
                if enabled {
                    ui.colored_label(egui::Color32::GREEN, "Running");
                } else {
                    ui.colored_label(egui::Color32::RED, "Stopped");
                }
                
                let mut intensity = current_intensity;
                if ui.add(egui::Slider::new(&mut intensity, 0.0..=100.0).suffix("%")).changed() {
                    self.app_state.update_attack_intensity(attack_type_clone.clone(), intensity);
                }
                
                if ui.button(if enabled { "Stop" } else { "Start" }).clicked() {
                    self.app_state.toggle_attack(attack_type_clone);
                }
                
                ui.end_row();
            }
        });
        
        ui.add_space(20.0);
        
        ui.heading("Recent Logs");
        ui.add_space(5.0);
        
        let logger = self.app_state.logger.clone();
        let logger = logger.lock().unwrap();
        let recent_logs = logger.get_recent_logs(5);
        
        if recent_logs.is_empty() {
            ui.label("No recent activity");
        } else {
            for log_entry in recent_logs {
                ui.label(format!("[{}] {}", 
                    log_entry.timestamp.format("%H:%M:%S"),
                    log_entry.message
                ));
            }
        }
    }
    
    fn render_attacks(&mut self, ui: &mut egui::Ui) {
        ui.heading("Attack Configuration");
        ui.add_space(20.0);
        
        ui.collapsing("DDoS Attack", |ui| {
            let enabled = self.app_state.attack_configs.get(&AttackType::DDoS).unwrap().enabled;
            let current_intensity = self.app_state.attack_configs.get(&AttackType::DDoS).unwrap().intensity;
            
            ui.horizontal(|ui| {
                if ui.button(if enabled { "Stop Attack" } else { "Start Attack" }).clicked() {
                    self.app_state.toggle_attack(AttackType::DDoS);
                }
                
                let mut config_enabled = enabled;
                if ui.checkbox(&mut config_enabled, "Enabled").changed() && config_enabled != enabled {
                    self.app_state.toggle_attack(AttackType::DDoS);
                }
            });
            
            ui.add_space(10.0);
            
            ui.label("Attack Intensity:");
            let mut intensity = current_intensity;
            if ui.add(egui::Slider::new(&mut intensity, 0.0..=100.0).suffix("%")).changed() {
                self.app_state.update_attack_intensity(AttackType::DDoS, intensity);
            }
            
            let packets_per_second = (intensity * 100.0) as u32;
            let bandwidth = packets_per_second as f32 * 1500.0 / 1024.0 / 1024.0; 
            
            ui.label(format!("Estimated metrics at current intensity:"));
            ui.label(format!("- Packets per second: {}", packets_per_second));
            ui.label(format!("- Bandwidth: {:.2} MB/s", bandwidth));
            
            ui.add_space(10.0);
            ui.separator();
            ui.add_space(10.0);
            
            ui.label("Description: Generates massive traffic with spoofed IPs to simulate a\nDistributed Denial of Service attack. This can be used to test\nnetwork infrastructure resilience and firewall configurations.");
        });
        
        ui.add_space(10.0);
        
        ui.collapsing("CPU Spike Attack", |ui| {
            let enabled = self.app_state.attack_configs.get(&AttackType::CPUSpike).unwrap().enabled;
            let current_intensity = self.app_state.attack_configs.get(&AttackType::CPUSpike).unwrap().intensity;
            
            ui.horizontal(|ui| {
                if ui.button(if enabled { "Stop Attack" } else { "Start Attack" }).clicked() {
                    self.app_state.toggle_attack(AttackType::CPUSpike);
                }
                
                let mut config_enabled = enabled;
                if ui.checkbox(&mut config_enabled, "Enabled").changed() && config_enabled != enabled {
                    self.app_state.toggle_attack(AttackType::CPUSpike);
                }
            });
            
            ui.add_space(10.0);
            
            ui.label("Attack Intensity:");
            let mut intensity = current_intensity;
            if ui.add(egui::Slider::new(&mut intensity, 0.0..=100.0).suffix("%")).changed() {
                self.app_state.update_attack_intensity(AttackType::CPUSpike, intensity);
            }
            
            ui.label(format!("Estimated metrics at current intensity:"));
            ui.label(format!("- CPU Usage: {:.1}%", intensity));
            ui.label(format!("- Active Threads: {}", (intensity / 10.0).ceil() as u32));
            
            ui.add_space(10.0);
            ui.separator();
            ui.add_space(10.0);
            
            ui.label("Description: Creates multiple threads that perform heavy calculations to\nmax out CPU usage. This can be used to test system resource monitoring,\nalerts, and auto-scaling capabilities.");
        });
        
        ui.add_space(10.0);
        
        ui.collapsing("Memory Leak Attack", |ui| {
            let enabled = self.app_state.attack_configs.get(&AttackType::MemoryLeak).unwrap().enabled;
            let current_intensity = self.app_state.attack_configs.get(&AttackType::MemoryLeak).unwrap().intensity;
            
            ui.horizontal(|ui| {
                if ui.button(if enabled { "Stop Attack" } else { "Start Attack" }).clicked() {
                    self.app_state.toggle_attack(AttackType::MemoryLeak);
                }
                
                let mut config_enabled = enabled;
                if ui.checkbox(&mut config_enabled, "Enabled").changed() && config_enabled != enabled {
                    self.app_state.toggle_attack(AttackType::MemoryLeak);
                }
            });
            
            ui.add_space(10.0);
            
            ui.label("Attack Intensity:");
            let mut intensity = current_intensity;
            if ui.add(egui::Slider::new(&mut intensity, 0.0..=100.0).suffix("%")).changed() {
                self.app_state.update_attack_intensity(AttackType::MemoryLeak, intensity);
            }
            
            let chunk_size_mb = intensity * 1024.0 * 1024.0 / 10.0 / 1024.0 / 1024.0;
            
            ui.label(format!("Estimated metrics at current intensity:"));
            ui.label(format!("- Memory Chunk Size: {:.2} MB per allocation", chunk_size_mb));
            ui.label(format!("- Maximum Memory Usage: 90% of system RAM"));
            
            ui.add_space(10.0);
            ui.separator();
            ui.add_space(10.0);
            
            ui.label("Description: Allocates memory progressively until reaching 90% of system RAM.\nThis can be used to test memory monitoring systems, OOM handling,\nand memory-based auto-scaling policies.");
        });
        
        ui.add_space(20.0);
        
        ui.heading("Combined Attacks");
        ui.add_space(10.0);
        
        if ui.button("Start All Attacks").clicked() {
            for attack_type in [AttackType::DDoS, AttackType::CPUSpike, AttackType::MemoryLeak].iter() {
                let config = self.app_state.attack_configs.get(attack_type).unwrap();
                if !config.enabled {
                    self.app_state.toggle_attack(attack_type.clone());
                }
            }
            
            let logger = self.app_state.logger.clone();
            let mut logger = logger.lock().unwrap();
            logger.log("Started combined attack (DDoS + CPU Spike + Memory Leak)".to_string());
        }
        
        if ui.button("Stop All Attacks").clicked() {
            for attack_type in [AttackType::DDoS, AttackType::CPUSpike, AttackType::MemoryLeak].iter() {
                let config = self.app_state.attack_configs.get(attack_type).unwrap();
                if config.enabled {
                    self.app_state.toggle_attack(attack_type.clone());
                }
            }
            
            let logger = self.app_state.logger.clone();
            let mut logger = logger.lock().unwrap();
            logger.log("Stopped all attacks".to_string());
        }
    }
    
    fn render_logs(&mut self, ui: &mut egui::Ui) {
        ui.heading("Attack Logs");
        ui.add_space(10.0);
        
        let logger = self.app_state.logger.clone();
        let logger = logger.lock().unwrap();
        let logs = logger.get_recent_logs(100);
        
        if logs.is_empty() {
            ui.label("No logs available");
        } else {
            egui::ScrollArea::vertical().max_height(500.0).show(ui, |ui| {
                for log_entry in logs.iter().rev() {
                    ui.horizontal(|ui| {
                        ui.label(format!("[{}]", log_entry.timestamp.format("%Y-%m-%d %H:%M:%S")));
                        ui.label(&log_entry.message);
                    });
                }
            });
        }
    }
    
    fn render_settings(&mut self, ui: &mut egui::Ui) {
        ui.heading("Communication Settings");
        ui.add_space(10.0);
        
        let comm_manager = self.app_state.comm_manager.clone();
        let mut comm_manager = comm_manager.lock().unwrap();
        
        ui.label("Protocol:");
        ui.horizontal(|ui| {
            if ui.radio_value(&mut comm_manager.protocol, Protocol::TCP, "TCP").clicked() {
                comm_manager.set_protocol(Protocol::TCP);
            }
            if ui.radio_value(&mut comm_manager.protocol, Protocol::UDP, "UDP").clicked() {
                comm_manager.set_protocol(Protocol::UDP);
            }
        });
        
        ui.add_space(10.0);
        
        ui.label("Port:");
        let mut port = comm_manager.port;
        if ui.add(egui::DragValue::new(&mut port).speed(1.0).clamp_range(1024..=65535)).changed() {
            comm_manager.set_port(port);
        }
        
        ui.add_space(20.0);
        ui.separator();
        ui.add_space(20.0);
        
        ui.heading("Acerca de");
        ui.label("Cyber Attack Simulator");
        ui.label("This tool is designed for educational purposes and security testing only.");
        ui.label("So uh, yeah, don't be dumb going all willy nilly trying to attack people");
        
        ui.add_space(10.0);
        ui.label("Features:");
        ui.label("- DDoS simulation with variable packet rates");
        ui.label("- CPU load testing with multi-threaded operations");
        ui.label("- Memory leak simulation with controlled allocation");
        ui.label("- Combined attack scenarios");
        ui.label("- Real-time metrics and logging");
        ui.label("- TCP/UDP communication with target systems");
        
        ui.add_space(20.0);
        ui.colored_label(egui::Color32::RED,
            "WARNING: This tool may or may not be as effective, idk man
            I'm going doing homework alright?
            You want a real tool? Look online
            Hell, use the Miku Miku Beam DDoS tool, it might be more effective "
        );
    }
}