# Import necessary modules and classes
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import sqlite3

# Create an instance of the FastAPI
app = FastAPI()

# Define Pydantic models for data validation and structure
# Task model for tasks API endpoint
class Task(BaseModel):
    title: str
    description: str
    due_date: str
    status: str
    priority: int = Field(ge=1, le=5, description="Task priority from 1 (highest) to 5 (lowest)")
    dependencies: List[str] = []

# ChatHistory model for chat history API endpoint (not used in current code)
class ChatHistory(BaseModel):
    summary: str

# UserFeedback model for feedback API endpoint
class UserFeedback(BaseModel):
    user_id: int
    feedback: str

# Database utility functions
# Function to connect to the database
def connect_db():
    return sqlite3.connect('memory.sqlite')

# Function to initialize the database with tables if they don't exist
def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()
    # Create table for tasks
    cursor.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT,
                      description TEXT,
                      due_date TEXT,
                      status TEXT,
                      dependencies TEXT)''')
    # Create table for chat history - not used but defined for future feature growth
    cursor.execute('''CREATE TABLE IF NOT EXISTS ChatHistory (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      summary TEXT)''')
    # Create table for feedback
    cursor.execute('''CREATE TABLE IF NOT EXISTS Feedback (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INT,
                      feedback TEXT)''')
    conn.commit()
    conn.close()

# Initialize the database (execute the above function)
initialize_db()

# Function to check if a task already exists in the database
def task_exists(title) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Tasks WHERE title = ?", (title,))
    task = cursor.fetchone()
    conn.close()
    return task is not None

# API route to get all tasks from the database
@app.get("/tasks")
def get_tasks():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tasks")
    tasks = [{
        "id": row[0], "title": row[1], "description": row[2],
        "due_date": row[3], "status": row[4],
        "dependencies": row[5].split(",") if row[5] else []
    } for row in cursor.fetchall()]  # Split dependencies by comma and convert to list
    conn.close()
    return tasks

# API route to create or update a task
@app.post("/tasks", status_code=201)
def manage_task(task: Task):
    conn = connect_db()
    cursor = conn.cursor()
    existing_task = task_exists(task.title)  # Check if task already exists
    if existing_task:
        # Update existing task
        cursor.execute("UPDATE Tasks SET description = ?, due_date = ?, status = ?, dependencies = ? WHERE title = ?",
                       (task.description, task.due_date, task.status, ','.join(task.dependencies), task.title))
    else:
        # Insert new task
        cursor.execute("INSERT INTO Tasks (title, description, due_date, status, dependencies) VALUES (?, ?, ?, ?, ?)",
                       (task.title, task.description, task.due_date, task.status, ','.join(task.dependencies)))
    conn.commit()
    task_id = cursor.lastrowid  # Get the ID of the created or updated task
    conn.close()
    return {"task_id": task_id, "message": "Task created or updated successfully."}

# API route to submit feedback to the database
@app.post("/feedback", status_code=201)
def submit_feedback(feedback: UserFeedback):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Feedback (user_id, feedback) VALUES (?, ?)",
                   (feedback.user_id, feedback.feedback))
    conn.commit()
    feedback_id = cursor.lastrowid  # Get the ID of the submitted feedback
    conn.close()
    return {"feedback_id": feedback_id, "message": "Feedback submitted successfully."}

# Default root API route
@app.get("/")
def read_root():
    # Simple welcome message
    return {"message": "Welcome to the ECO-FMM-FASTAPI v1.1"}

# Main entry point for running the app
if __name__ == "__main__":
    import uvicorn
    # Start the server on host 0.0.0.0 and port 80, reloading is off for production
    uvicorn.run(app, host="0.0.0.0", port=80, reload=False)
