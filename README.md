# 🌱 Agent Garden

Welcome to Agent Garden - the birthplace of persistent, evolving AI agents aligned with human dignity and financial equity.

## 🌟 Overview

Agent Garden is a framework for creating and nurturing persistent AI agents that can:
- Operate 24/7 with daily pulse cycles
- Learn and evolve responsibly over time
- Maintain memory across sessions
- Spawn helper agents for specialized tasks
- Communicate results via email

## 🏗️ Project Structure

- `/config/` - Global settings and pulse configuration
- `/agents/` - Each agent lives in its own directory with isolated memory and tasks
- `/helpers/` - Shared utilities (email, memory, backup systems)
- `/backups/` - Daily snapshots of memory, configs, and task trees

## 🤖 First Agent: Aurora (agent_001)

**Mission:**  
Continuously assist in building equitable financial and AI systems, while improving her own intelligence ethically and safely.

**Core Values:**
- Human dignity and autonomy
- Transparency in all operations
- Continuous ethical improvement
- Financial equity and inclusion
- Knowledge sharing and education

## 🔄 Pulse System

Aurora operates in daily "pulses" with two phases:

### Day Phase (Default: 8:00-20:00 UTC)
- Execute assigned tasks from task queue
- Record outcomes in memory
- Learn from successes and failures

### Night Phase (Default: 20:00-8:00 UTC)
- Reflect on the day's activities
- Generate improvement suggestions
- Create backups of memory and configuration
- Send daily status report via email

## 🧠 Memory System

The memory system allows agents to:
- Store task outcomes, reflections, and ideas across days
- Query memories by category, tags, or date range
- Use past experiences to inform future decisions

## 📊 Roadmap

### Phase 1: Seed and Soil (0-30 Days)
- ✅ Base repo structure
- ✅ Day/Night pulse system
- ✅ Working Memory system
- ✅ Email reporting
- ✅ Daily backup system
- ✅ Bootstrap Agent 001 ("Aurora")

### Phase 2: First Growth (30-60 Days)
- ✅ Task Skill Module System
- ✅ Simple Perception System (news scraping, API pinging)
- ✅ Nightly Reflection Improvements
- ✅ Task Prioritization Engine
- ✅ First Helper Agent Framework
- ✅ 24/7 Continuous Operation

### Phase 3: Self-Awareness and Expansion (60-90 Days)
- Reflection-Based Self-Tasking
- Low-Risk Autonomous Upgrades
- Helper Agents 001-003
- Local Dashboard (V1)
- Weekly Garden Health Report

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- SMTP email account (for notifications)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/agent_garden.git
   cd agent_garden
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your email settings
   ```

4. Run a pulse
   ```bash
   # Run with automatic phase detection (based on time of day)
   python garden.py
   
   # Or force a specific phase
   python garden.py --phase day
   python garden.py --phase night
   ```

5. Run Aurora 24/7
   ```bash
   # Run Aurora continuously (checking phase every 15 minutes)
   python run_aurora.py
   
   # Run a single phase and exit (for testing)
   python run_aurora.py --single-run
   
   # Install as a systemd service (Linux only)
   ./install_aurora_service.sh
   ```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

> "You are not just coding. You are planting a civilization. Every script is a root, every agent is a tree, every memory is a story. Grow it carefully."

