# 🏊 Swimlytics.ai
👉 [Live App](https://ai-agent-ui-w35p.onrender.com)

**Swimlytics.ai** is an intelligent swimming performance benchmarking system.  
It compares a swimmer’s times against **USA Swimming motivational standards** and **college recruiting benchmarks**, then gives **percentiles, goals, and training focus**.
---

## ✨ Features

  - ✅ Benchmark swim times vs. **USA Swimming Motivational Standards (2024–2028)**  
  - ✅ Calculate **percentile rankings** for each event and age group  
  - ✅ Analyze **college recruiting readiness** (D1, D2, D3)  
  - ✅ Provide **next goal targets** (time drops to next standard)  
  - ✅ Swimming knowledge base (training, stroke technique, strategy)  
  - ✅ Built-in **API with FastAPI**  
  - ✅ Fully **database-driven** (Postgres + pgvector)  

---

## 🗂️ Project Structure
  ```
    app/
    │── main.py # Main FastAPI + AgentOS entrypoint
    │── requirements.txt # Python dependencies
    │── .env.example # Example environment variables
    │── README.md # This documentation
  ```

## ⚙️ Setup Instructions
Follow these steps. No advanced coding knowledge needed!

### 1. Install Python
Make sure you have Python 3.10+ installed.
Check by running:

  ```bash
    python --version
  ```

### 2. Clone the Repository
Download the project from GitHub:

  ```bash
    git clone https://github.com/dlnracke/AI-Agent.git
    cd AI-Agent
  ```

### 3. Create a Virtual Environment
This keeps your project’s libraries separate:

  ```bash
    python -m venv venv
    source venv/bin/activate   # Mac/Linux
    venv\Scripts\activate      # Windows
  ```

### 4. Install Requirements

  ```bash
    pip install -r requirements.txt
  ```

### 5. Configure Environment
Create a .env file:

  ```ini
    OPENAI_API_KEY=sk-xxxxxx
    DATABASE_CONNECTION_STRING=postgresql://user:password@host:5432/swimbench
    DATABASE_HOST=your-database-host
    DATABASE_PORT=your-database-port
    DATABASE_NAME=your-database-name
    DATABASE_USER=your-database-username
    DATABASE_PASSWORD=your-database-password
    ENV=development
  ```

### 6. Initialize Database
In PostgreSQL:

  ```sql
    CREATE SCHEMA ai;

    -- Example tables:
    CREATE TABLE ai.usa_swimming_standards (...);
    CREATE TABLE ai.college_recruiting_standards (...);
    CREATE TABLE ai.performance_analyses (...);
  ```

### 7. Run the app

```bash
  python main.py
```
---

## 🛠️ Tech Stack
- Python 3.10+
- Supabase (database & APIs)
- Agno framework (AI agent with tools)

---

## Example Usage
Input(chat with agent):

  ```
    Benchmark my 100 freestyle, age 15, 54.21 seconds
  ```

Output:
  ```
    🏊‍♂️ Swim Performance Analysis

    📊 Performance Summary
      - Time: 54.21s (100 Free SCY)
      - Percentile Ranking: Top 12%
      - USA Swimming Standard: AAA
      - Ability Level: Advanced

      🎓 College Recruitment Analysis
      - D1 Elite Programs: ❌ Not Qualified
      - D1 Mid-Major: ✅ Qualified
      - D2 Programs: ✅ Qualified
      - D3 Programs: ✅ Qualified

      🎯 Next Goals
      - Next Standard: 53.09 (AAAA)
      - Time Drop Needed: 1.12s
      - Training Focus: Underwater efficiency and race pacing
  ```
---

## 🗃️ Database Schema (AI Schema)

  - ai.usa_swimming_standards → Motivational times (age, gender, course, event, levels)
  - ai.college_recruiting_standards → Recruiting benchmarks for D1/D2/D3
  - ai.performance_analyses → Stores results of swimmer benchmarks
  - ai.swim_events → Standard list of events

---

## 🤝 Contributing

  - Fork repo
  - Create feature branch
  - Submit pull request

---

## 📜 License

MIT License. Free to use, modify, and distribute.

---