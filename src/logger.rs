use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::Path;
use chrono::{DateTime, Local};

pub struct Logger {
    log_entries: Vec<LogEntry>,
    log_file: Option<File>,
}

#[derive(Clone, Debug)]
pub struct LogEntry {
    pub timestamp: DateTime<Local>,
    pub message: String,
}

impl Logger {
    pub fn new() -> Self {
        let logs_dir = Path::new("logs");
        if !logs_dir.exists() {
            std::fs::create_dir(logs_dir).unwrap_or_else(|_| {
                eprintln!("Failed to create logs directory");
            });
        }

        let now = Local::now();
        let filename = format!("logs/attack_log_{}.txt", now.format("%Y%m%d_%H%M%S"));
        
        let log_file = OpenOptions::new()
            .write(true)
            .create(true)
            .append(true)
            .open(&filename)
            .unwrap_or_else(|_| {
                eprintln!("Failed to create log file");
                File::create("attack_log_fallback.txt").expect("Failed to create fallback log file")
            });

        Self {
            log_entries: Vec::new(),
            log_file: Some(log_file),
        }
    }

    pub fn log(&mut self, message: String) {
        let entry = LogEntry {
            timestamp: Local::now(),
            message,
        };
        
        println!("[{}] {}", entry.timestamp.format("%H:%M:%S"), entry.message);
        
        if let Some(file) = &mut self.log_file {
            let log_line = format!("[{}] {}\n", entry.timestamp.format("%Y-%m-%d %H:%M:%S"), entry.message);
            if let Err(e) = file.write_all(log_line.as_bytes()) {
                eprintln!("Failed to write to log file: {}", e);
            }
        }
        
        self.log_entries.push(entry);
        
        if self.log_entries.len() > 100 {
            self.log_entries.remove(0);
        }
    }

    pub fn get_recent_logs(&self, count: usize) -> Vec<LogEntry> {
        let start = if self.log_entries.len() > count {
            self.log_entries.len() - count
        } else {
            0
        };
        
        self.log_entries[start..].to_vec()
    }

}

impl Clone for Logger {
    fn clone(&self) -> Self {
        Self {
            log_entries: self.log_entries.clone(),
            log_file: None, 
        }
    }
}