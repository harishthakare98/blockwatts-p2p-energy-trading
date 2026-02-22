⚡ BlockWatts
Peer-to-Peer Renewable Energy Trading Platform








🌍 Overview

BlockWatts is a scalable Peer-to-Peer (P2P) Renewable Energy Trading Platform that simulates real-world energy markets using a mock wallet system.

The platform allows users to:

⚡ List surplus renewable energy (kWh)

💰 Buy energy from other users

📊 Analyze market trends

🔄 Track transactions in real time

🏦 Manage virtual wallet balance

This project demonstrates backend system design, trading engine logic, wallet architecture, and scalable deployment strategy using Django.

🎯 Problem Statement

Renewable energy producers often generate surplus power that goes unused.
Traditional grids are centralized and inefficient for peer-level trading.

BlockWatts solves this by simulating a decentralized energy marketplace where individuals can trade renewable energy transparently and efficiently.

🚀 Key Features
🔐 Authentication System

Secure user registration & login

Session-based authentication

💰 Mock Wallet System

Virtual balance management

Debit/Credit transaction handling

Real-time balance validation

⚡ Energy Marketplace

List energy in kWh

Set price per unit

View available listings

Buy directly from sellers

🔄 Order Matching Engine

Validates wallet balance

Checks energy availability

Executes transaction atomically

Updates seller & buyer wallets

📈 Market Analytics Dashboard

Total traded energy

Active listings

Transaction insights

Market volume tracking

🏭 Smart Meter Integration (Planned)

API-based smart meter simulation

Automated energy data fetching

Real-time production syncing

🏗 System Architecture
User
  ↓
Django Backend
  ↓
Trading Engine
  ↓
Wallet System
  ↓
Database (PostgreSQL)

Future Scope:

Smart Meter API → Trading Engine → Blockchain Ledger
🛠 Tech Stack
Layer	Technology
Backend	Django
Language	Python
Database	PostgreSQL
API	Django REST Framework
Deployment	Docker (Planned)
Version Control	Git & GitHub
📂 Project Structure
blockwatts/
│
├── apps/
│   ├── users/
│   ├── wallet/
│   ├── energy_market/
│   ├── transactions/
│   └── analytics/
│
├── templates/
├── static/
├── docs/
└── manage.py
⚙️ Installation Guide
1️⃣ Clone Repository
git clone https://github.com/harishthakare98/blockwatts-p2p-energy-trading.git
cd blockwatts-p2p-energy-trading
2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate
3️⃣ Install Dependencies
pip install -r requirements.txt
4️⃣ Run Migrations
python manage.py migrate
5️⃣ Start Server
python manage.py runserver

Visit:

http://127.0.0.1:8000/
🔮 Future Enhancements

🔗 Blockchain-based transaction ledger

📡 Real Smart Meter Integration

🤖 AI-based Demand & Price Forecasting

📊 Advanced Data Visualization

☁️ Production Deployment with Nginx & Docker

📈 Load Balancing & Scalability Optimization

🧠 Learning Outcomes

This project demonstrates:

Backend Architecture Design

Transaction Atomicity Handling

Wallet Logic Implementation

Order Matching Algorithms

Database Modeling

System Scalability Planning

Clean Git Workflow

📌 Use Case Scenarios

Renewable Energy Startups

Smart Grid Simulations

Academic Research Projects

Hackathon Submissions

FinTech + EnergyTech Applications

👨‍💻 Author

Harish Thakare
B.Tech CSE Student
Passionate about Renewable Energy Technology & Scalable Systems

⭐ Support

If you like this project:

⭐ Star the repository

🍴 Fork it

🚀 Contribute to improve
