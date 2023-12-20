# Import necessary modules and classes
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3

# Create FastAPI app instance
app = FastAPI()

# Define Pydantic models for data validation

# A Task model to create or update tasks with title, description, due date, status, priority, and dependencies
class Task(BaseModel):
    title: str
    description: str
    dueDate: str
    status: str
    # Field with validation to ensure the priority is between 1 (highest) and 5 (lowest)
    priority: int = Field(ge=1, le=5, description="Task priority from 1 (highest) to 5 (lowest)") 
    dependencies: List[str] = []

# A ChatHistory model for storing chat summaries
class ChatHistory(BaseModel):
    summary: str

# A UserFeedback model to store user feedback with the user ID and the feedback content
class UserFeedback(BaseModel):
    user_id: int
    feedback: str

# Database utility functions

# Function to establish a SQLite database connection
def connect_db():
    return sqlite3.connect('memory.sqlite')

# Function to initialize the necessary tables in the SQLite database if they do not exist
def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()
    # Table for tasks
    cursor.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT,
                      description TEXT,
                      dueDate TEXT,
                      status TEXT,
                      dependencies TEXT)''')
    # Table for chat history
    cursor.execute('''CREATE TABLE IF NOT EXISTS ChatHistory (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      summary TEXT)''')
    # Table for user feedback
    cursor.execute('''CREATE TABLE IF NOT EXISTS Feedback (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INT,
                      feedback TEXT)''')
    conn.commit()
    conn.close()

# Initialize the database as soon as the app starts
initialize_db()

# Function to check if a task exists based on its title
def task_exists(title) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Tasks WHERE title = ?", (title,))
    task = cursor.fetchone()
    conn.close()
    return task

# FastAPI route handlers

# Endpoint to retrieve all tasks
@app.get("/tasks")
def get_tasks():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Tasks")
        tasks = [{"id": row[0], "title": row[1], "description": row[2], "dueDate": row[3], "status": row[4], "dependencies": row[5]} for row in cursor.fetchall()]
        conn.close()
        return tasks
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

# Endpoint to create a new task or update an existing one based on its title
@app.post("/tasks", status_code=201)
def manage_task(task: Task):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if a task with the provided title exists
        existing_task = task_exists(task.title)
        if existing_task:
            # If task exists, update the existing task
            cursor.execute("UPDATE Tasks SET description = ?, dueDate = ?, status = ?, dependencies = ? WHERE title = ?",
                           (task.description, task.dueDate, task.status, ','.join(task.dependencies), task.title))
            task_id = existing_task[0]
        else:
            # If task does not exist, insert a new task
            cursor.execute("INSERT INTO Tasks (title, description, dueDate, status, dependencies) VALUES (?, ?, ?, ?, ?)",
                           (task.title, task.description, task.dueDate, task.status, ','.join(task.dependencies)))
            task_id = cursor.lastrowid

        conn.commit()
        return {"task_id": task_id, "message": "Task created or updated successfully."}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        # Ensure the database connection is closed
        if conn:
            conn.close()

# Other endpoints would be similar to the ones above and can be commented
# accordingly when their logic is defined.

# Root endpoint to display a welcome message
@app.get("/")
def read_root():
    return {"message": "Welcome to the ECO-FMM-FASTAPI v1.0"}

# Main function which runs only if this script is executed as the main program
if __name__ == "__main__":
    # Using Uvicorn to serve the application
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80, reload=False)