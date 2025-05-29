use std::net::{TcpListener, TcpStream, UdpSocket};
use std::io::Write;
use std::thread;
use std::sync::{Arc, Mutex};
use serde_json;
use crate::AttackMetrics;

#[derive(PartialEq, Clone, Copy)]  
pub enum Protocol {
    TCP,
    UDP
}

pub struct CommunicationManager {
    pub protocol: Protocol,  
    pub port: u16,          
    running: Arc<Mutex<bool>>,
}

impl CommunicationManager {
    pub fn new() -> Self {
        Self {
            protocol: Protocol::TCP,
            port: 8080,
            running: Arc::new(Mutex::new(false)),
        }
    }

    pub fn start(&mut self) -> Result<(), String> {
        let mut running = self.running.lock().unwrap();
        *running = true;
        drop(running);

        match self.protocol {
            Protocol::TCP => self.start_tcp_server(),
            Protocol::UDP => self.start_udp_server(),
        }
    }

    fn start_tcp_server(&self) -> Result<(), String> {
        let listener = match TcpListener::bind(format!("127.0.0.1:{}", self.port)) {
            Ok(listener) => listener,
            Err(e) => return Err(format!("Failed to bind TCP socket: {}", e)),
        };

        let running = self.running.clone();
        
        thread::spawn(move || {
            listener.set_nonblocking(true).expect("Failed to set non-blocking");
            
            while *running.lock().unwrap() {
                match listener.accept() {
                    Ok((stream, _)) => {
                        handle_tcp_connection(stream);
                    }
                    Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        thread::sleep(std::time::Duration::from_millis(100));
                        continue;
                    }
                    Err(e) => {
                        eprintln!("Failed to accept connection: {}", e);
                        break;
                    }
                }
            }
        });

        Ok(())
    }

    fn start_udp_server(&self) -> Result<(), String> {
        let socket = match UdpSocket::bind(format!("127.0.0.1:{}", self.port)) {
            Ok(socket) => socket,
            Err(e) => return Err(format!("Failed to bind UDP socket: {}", e)),
        };

        let running = self.running.clone();
        
        thread::spawn(move || {
            socket.set_nonblocking(true).expect("Failed to set non-blocking");
            
            let mut buf = [0; 1024];
            
            while *running.lock().unwrap() {
                match socket.recv_from(&mut buf) {
                    Ok((size, src)) => {
                        let data = String::from_utf8_lossy(&buf[0..size]);
                        println!("Received from {}: {}", src, data);
                        
                        let response = "Attack metrics received";
                        let _ = socket.send_to(response.as_bytes(), src);
                    }
                    Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        thread::sleep(std::time::Duration::from_millis(100));
                        continue;
                    }
                    Err(e) => {
                        eprintln!("Failed to receive data: {}", e);
                        break;
                    }
                }
            }
        });

        Ok(())
    }

    pub fn stop(&mut self) {
        let mut running = self.running.lock().unwrap();
        *running = false;
    }

    pub fn set_protocol(&mut self, protocol: Protocol) {
        self.protocol = protocol;
    }

    pub fn set_port(&mut self, port: u16) {
        self.port = port;
    }

    pub fn send_metrics(&self, metrics: &AttackMetrics) {
        let json_metrics = serde_json::to_string(metrics).unwrap_or_else(|_| {
            String::from("{\"error\": \"Failed to serialize metrics\"}")
        });
        
        match self.protocol {
            Protocol::TCP => {
                if let Ok(mut stream) = TcpStream::connect(format!("127.0.0.1:{}", self.port)) {
                    let _ = stream.write_all(json_metrics.as_bytes());
                }
            },
            Protocol::UDP => {
                if let Ok(socket) = UdpSocket::bind("127.0.0.1:0") {
                    let _ = socket.send_to(
                        json_metrics.as_bytes(),
                        format!("127.0.0.1:{}", self.port)
                    );
                }
            }
        }
    }
}

fn handle_tcp_connection(mut stream: TcpStream) {
    let response = "Connection established to attack simulator";
    let _ = stream.write_all(response.as_bytes());
}