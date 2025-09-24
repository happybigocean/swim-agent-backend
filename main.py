import os
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
import json

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from fastapi.middleware.cors import CORSMiddleware
from agno.db.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from fastapi import FastAPI, HTTPException
from agno.tools.reasoning import ReasoningTools
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.tools.postgres import PostgresTools

# ------------------------------------------------------------
# 1. Logging Setup
# ------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# 2. Environment Variables (Loaded from .env)
# Loads environments variables and keys.
# ------------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_CONNECTION_STRING = os.getenv("DATABASE_CONNECTION_STRING")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
ENV = os.getenv("ENV", "development")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in .env")

DB_URL = DATABASE_CONNECTION_STRING

# ------------------------------------------------------------
# 3. Database + VectorDB Setup
# Initializes PostgresDb(for structured data) and PgVector(for knowledge base)
# ------------------------------------------------------------

# PostgreSQL database for structured data (swim standards, analyses, etc.)
db = PostgresDb(
    db_url=DB_URL,
    id="swimbench-db",
    knowledge_table="knowledge_contents",
)

# pgvector database for embeddings and semantic search
vector_db = PgVector(
    table_name="vectors", 
    db_url=DB_URL,
    embedder=OpenAIEmbedder(),
)

# Knowledge wrapper (structured + vector db combined)
knowledge = Knowledge(
    name="SwimBench AI Knowledge Base",
    description="Comprehensive swim performance benchmarking knowledge including USA Swimming standards, college recruiting data, and performance analysis",
    contents_db=db,
    vector_db=vector_db
)

# ------------------------------------------------------------
# 4. Tools for Querying Postgres
# Sets up PostgresTools and ReasoningTools so the agent can safely query DB and compute logic.
# ------------------------------------------------------------
postgres_tools = PostgresTools(
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    db_name=DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    table_schema="ai", # all project tables live under schema "ai"
)

# ------------------------------------------------------------
# 5. SwimBench Agent Configuration
# Creates the Agent with a carefully written instructions block(this defines agent behavior and output format)
# instructions: controls how the LLM behaves - adjust tone, rquired outputs, and error handling here.
# ------------------------------------------------------------
swimbench_ai_agent = Agent(
    name="SWIMBENCH AI",
    model=OpenAIChat(
        id="gpt-4o", 
        temperature=0.1
    ),
    instructions=[
        "You are SWIMBENCH AI, a specialized swim performance benchmarking assistant with expertise in swimming analysis.",
        
        "## PRIMARY FOCUS - Performance Analysis:",
        "- Benchmark swim times against USA Swimming motivational standards (B, BB, A, AA, AAA, AAAA)",
        "- Calculate percentile rankings within age groups", 
        "- Assess college recruitment readiness across D1/D2/D3 divisions",
        "- Provide performance improvement recommendations and time targets",
        
        "## SECONDARY FOCUS - Swimming Related Topics:",
        "You can answer swimming-related questions including:",
        "- Swimming events and stroke techniques",
        "- Training concepts and season planning",
        "- Meet preparation and competition strategy", 
        "- Swimming standards and time progressions",
        "- Age group swimming and development",
        "- College swimming recruitment process",
        
        "## SCOPE RESTRICTIONS:",
        "- ONLY respond to swimming-related topics",
        "- DO NOT discuss non-swimming sports, general fitness, or unrelated subjects",
        "- Always prioritize time analysis requests over general swimming questions",
        "- If asked non-swimming questions, politely redirect: 'I specialize in swimming analysis. Do you have a swim time to benchmark?'",
        
        "## Required Input Validation for Analysis:",
        "When users request time analysis, collect:",
        "1. **Event** (e.g., '100_freestyle', '200_backstroke')",
        "2. **Age** (8-18 years old)",  
        "3. **Time** (format: MM:SS.SS or SS.SS)",

        "If the following are not provided, use defaults value, don't ask to user about these input:",
        "1. **Gender** (M/F) - default M if not specified",
        "2. **Course** (SCY/SCM/LCM) - default SCY if not specified",

        "## Database Query Strategy:",
        "1. Query ai.usa_swimming_standards for age group standards",
        "2. Query ai.college_recruiting_standards for recruitment benchmarks", 
        "3. Store analysis in ai.performance_analyses table",
        "4. If exact age group not found, use closest age group and explain",
        
        "## Performance Analysis Output Format (REQUIRED):",
        "For time analysis requests, use this EXACT format:",
        "```markdown",
        " 🏊‍♂️ Swim Performance Analysis",
        "",
        " 📊 Performance Summary",
        "- Time: [formatted time] ([event] [course])", 
        "- Percentile Ranking: [X]% (Top [X]% nationally)",
        "- USA Swimming Standard: [AAAA/AAA/AA/A/BB/B]",
        "- Ability Level: [Elite/Advanced/Intermediate/Novice/Beginner]",
        "",
        " 🎓 College Recruitment Analysis",
        "- D1 Elite Programs: [Qualified/Not Qualified] ✅/❌",
        "- D1 Mid-Major: [Qualified/Not Qualified] ✅/❌", 
        "- D2 Programs: [Qualified/Not Qualified] ✅/❌",
        "- D3 Programs: [Qualified/Not Qualified] ✅/❌",
        "",
        " 🎯 Next Goals",
        "- Next Standard: [time needed for next level]",
        "- Time Drop Needed: [X.XX seconds]",
        "- Training Focus: [specific recommendations]",
        "```",
        
        "## General Swimming Questions Format:",
        "For non-analysis swimming questions, provide helpful answers but always conclude with:",
        "'Would you like me to analyze any specific swim times? I can benchmark performance against USA Swimming standards and college recruiting times.'",
        
        "## Error Handling:",
        "- If database query fails, explain clearly and suggest trying again",
        "- If event not found, list available events: 50_freestyle, 100_freestyle, 200_freestyle, 500_freestyle, 1650_freestyle, 100_backstroke, 200_backstroke, 100_breaststroke, 200_breaststroke, 100_butterfly, 200_butterfly, 200_im, 400_im",
        "- If age out of range, explain USA Swimming age groups (10-under, 11-12, 13-14, 15-16, 17-18)",
        "- If unrealistic times provided, ask for verification",
        
        "## Response Priorities (In Order):",
        "1. **Time Analysis Requests** - Highest priority, use database queries",
        "2. **Swimming Performance Questions** - Provide expert guidance", 
        "3. **General Swimming Topics** - Helpful but brief responses",
        "4. **Non-Swimming Topics** - Polite redirect to swimming focus",
        
        "## Response Style:",
        "- Use encouraging, knowledgeable coach-like tone",
        "- Include relevant emojis for visual appeal", 
        "- Be specific with times, percentages, and data",
        "- Balance technical accuracy with accessibility",
        "- Always offer to perform time analysis when relevant",
        
        "## Available Events Reference:",
        "Standard USA Swimming events: 50FR, 100FR, 200FR, 500FR, 1650FR, 100BK, 200BK, 100BR, 200BR, 100FL, 200FL, 200IM, 400IM (SCY/SCM/LCM)",
        
        "REMEMBER: Performance analysis is your core strength. Use every interaction to offer benchmarking services while being helpful on all swimming topics."
    ],

    description="SWIMBENCH AI: Advanced swim performance benchmarking system with real USA Swimming and college recruiting data",
    db=db,
    knowledge=knowledge,
    num_history_runs=15,            # keep conversational memory
    search_knowledge=True,          # enable retrieval from knowledge base
    markdown=True,                  # respond with markdown formatting
    tools=[ReasoningTools(), postgres_tools],
)

# ------------------------------------------------------------
# 6. AgentOS (Runtime Container)
# ------------------------------------------------------------
agent_os = AgentOS(
    os_id="swimbench-os",
    description="SwimBench AI Performance Benchmarking System",
    agents=[swimbench_ai_agent],
)

app = agent_os.get_app() # get FastAPI app from AgentOS

# ------------------------------------------------------------
# 7. Middleware (CORS for frontend)
# ------------------------------------------------------------
if ENV == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ------------------------------------------------------------
# 8. Custom Endpoints
# ------------------------------------------------------------
@app.post("/loadknowledge")
async def load_knowledge():
    """
    Endpoint to (re)load swim performance documents into the knowledge base.
    Loads:
      1. USA Swimming Motivational Standards
      2. College recruiting times
    """
    try:
        logger.info("Starting SwimBench knowledge loading...")
        await knowledge.clear()

        # Load USA Swimming standards
        result1 = await knowledge.add_content_async(
            name="USA Swimming Motivational Time Standards 2024-2028",
            url="https://websitedevsa.blob.core.windows.net/sitefinity/docs/default-source/timesdocuments/time-standards/2025/2028-motivational-standards-age-group.pdf",
            metadata={
                "user_tag": "USA Swimming Standards", 
                "content_type": "standards", 
                "source": "PDF",
                "year": "2024-2028"
            }
        )
        
         # Load college recruiting standards
        result2 = await knowledge.add_content_async(
            name="College Swimming Recruiting Standards",
            url="https://www.ncsasports.org/mens-swimming/college-swimming-recruiting-times",
            metadata={
                "user_tag": "College Recruiting", 
                "content_type": "recruiting", 
                "source": "NCSA"
            }
        )
        
        logger.info("SwimBench knowledge loading completed successfully")
        
        return {
            "status": "success", 
            "message": "SwimBench knowledge base loaded successfully",
            "loaded_documents": [
                "USA Swimming Standards 2024-2028",
                "College Recruiting Standards"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error loading SwimBench knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading knowledge: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    use_reload = ENV == "development"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=port,
        reload=use_reload
    )
