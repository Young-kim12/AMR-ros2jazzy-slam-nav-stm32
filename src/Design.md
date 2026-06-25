# 📑 Detailed Design Document: Project COMMAND CENTER

---

## 1. High-Level Architecture and Data Flow

### 1.1. System Layer Overview

The system follows a **three-layer architecture** of **Perception – Cognition/Decision – Actuation**.  
Data flows downward through these layers, transforming from sensed information into physical actions.

![Three-layer system architecture diagram](image_placeholder)

---

### 1.2. Main Data Flow

1. **AI Vision Server:**  
   Performs production line image analysis → Generates real-time **inventory status** data → Publishes to **MQTT broker**.

2. **AMR (Raspberry Pi):**  
   Subscribes to inventory status → Merges with internal **map/path data** → Determines **optimal mission and route** → Sends commands to the motor controller.

3. **Motor Controller (STM32):**  
   Converts received commands into **PWM motor control signals** → Drives AMR motion and executes pallet handling.

---

## 2. Module Design

### 2.1. Path Optimization and Mission Assignment Module (Raspberry Pi)

| Design Element | Details |
| :--- | :--- |
| **Core Algorithm** | **A\*** (A-star) algorithm for pathfinding (shortest path and obstacle avoidance) |
| **Input Data** | Real-time inventory status (MQTT), AMR position (IMU/GPS), digital map data |
| **Output Data** | Step-wise motion commands (Velocity, Angle), serial communication commands to motor controller |
| **Languages/Frameworks** | Python, ROS (Robot Operating System) |

---

### 2.2. Motor Control Driver (STM32)

- **Primary Role:**  
  Converts commands received from Raspberry Pi into **PWM signals** for precise motor control.

- **Communication Interface:**  
  Communicates with Raspberry Pi via **UART**, receiving commands based on a defined protocol.

- **Control Method:**  
  Implements a **PID control loop** to maintain stable motor speed and position feedback.

---

## 3. Data Structure Definition

### 3.1. Inventory Status Message (AI Server → AMR)

| Field | Type | Description |
| :--- | :--- | :--- |
| `line_id` | String | Production line identifier |
| `item_id` | String | Predicted depleted part ID |
| `predict_time` | Float | Remaining time until depletion (seconds) |
| `priority` | Int | Task priority level (1–5) |

---

### 3.2. AMR Motion Command (AMR → Motor Controller)

| Field | Type | Description |
| :--- | :--- | :--- |
| `linear_vel` | Float | Linear velocity (m/s) |
| `angular_vel` | Float | Angular velocity (rad/s) |
| `lift_command` | Boolean | Lift operation trigger (True/False) |
