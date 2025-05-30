# Cyber Attack Simulator

A Rust-based educational tool designed for simulating various cyber attacks in a controlled environment. This application provides a graphical interface for testing system resilience, monitoring capabilities, and security response procedures.

## What It Is

The Cyber Attack Simulator is a desktop application built with Rust and eframe/egui that simulates three types of common cyber attacks:

- **DDoS (Distributed Denial of Service)**: Simulates massive network traffic with spoofed IP addresses
- **CPU Spike Attack**: Creates high CPU load through multi-threaded intensive calculations
- **Memory Leak Attack**: Progressively allocates memory to simulate memory exhaustion scenarios

## What It Does

### Core Features
- **Real-time Attack Simulation**: Execute simulated attacks with configurable intensity levels
- **Interactive Dashboard**: Monitor active attacks, network traffic, CPU usage, and memory allocation
- **Logging System**: Track all attack activities with timestamped logs saved to files
- **Communication Module**: TCP/UDP server capabilities for metrics transmission
- **Safety Controls**: Built-in safeguards to prevent actual system damage (memory usage capped at 90% of system RAM)

### Attack Types
1. **DDoS Simulation**
   - Generates network packets with randomized source IP addresses
   - Configurable packet rate (0-100 packets/second per intensity percentage)
   - Bandwidth usage estimation and monitoring

2. **CPU Load Testing**
   - Multi-threaded mathematical operations to consume CPU resources
   - Scales thread count based on available CPU cores and intensity
   - Real-time CPU usage monitoring

3. **Memory Allocation Testing**
   - Progressive memory allocation in configurable chunks
   - Safety threshold prevents system instability
   - Memory usage tracking and reporting

### User Interface
- **Dashboard Tab**: Overview of all active attacks and system metrics
- **Attacks Tab**: Individual attack configuration and control
- **Logs Tab**: Historical attack activity and system events
- **Settings Tab**: Communication protocol configuration (TCP/UDP)

## Requirements

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB+ recommended for memory leak testing)
- **CPU**: Multi-core processor recommended for CPU spike testing

### Development Requirements
- **Rust**: Version 1.70 or higher
- **Cargo**: Rust package manager (included with Rust installation)

### Dependencies
The following Rust crates are required (automatically handled by Cargo):
- `eframe 0.22.0` - GUI framework
- `chrono 0.4` - Date and time handling
- `serde 1.0` - Serialization framework
- `serde_json 1.0` - JSON serialization
- `num_cpus 1.13` - CPU count detection
- `sys-info 0.9` - System information
- `env_logger 0.10` - Logging functionality
- `rand 0.8` - Random number generation
- `winapi 0.3` - Windows API bindings (Windows only)

## Installation and Usage

### Building from Source
1. Clone or download the project files
2. Navigate to the project directory
3. Build and run the application:
   ```bash
   cargo run
   ```

### Running the Application
1. Launch the executable
2. Use the Dashboard tab to get an overview of system status
3. Navigate to the Attacks tab to configure and start individual attacks
4. Monitor logs in the Logs tab
5. Adjust communication settings in the Settings tab

### Safety Notes
- The application includes built-in safety mechanisms to prevent system damage
- Memory allocation is limited to 90% of available system RAM
- All attacks are simulated and contained within the application
- Logs are automatically saved to the `logs/` directory

## Educational Purpose

This tool is designed exclusively for:
- Educational demonstrations of cyber attack principles
- Security testing and system resilience evaluation
- Training security professionals and students
- Testing monitoring and alerting systems
- Evaluating system resource management

## Disclaimer

This software is intended for educational and authorized testing purposes only. Users are solely responsible for ensuring compliance with all applicable laws and regulations. The developers assume no responsibility for misuse of this software.
