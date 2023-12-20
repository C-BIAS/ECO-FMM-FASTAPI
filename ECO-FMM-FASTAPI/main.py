
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3

app = FastAPI()

# Pydantic models
class Task(BaseModel):
    title: str
    description: str
    dueDate: str
    status: str
    dependencies: List[str] = []

class ChatHistory(BaseModel):
    summary: str

class UserFeedback(BaseModel):
    user_id: int
    feedback: str

# Database connection
def connect_db():
    return sqlite3.connect('memory.sqlite')

# Initialize database
def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT,
                      description TEXT,
                      dueDate TEXT,
                      status TEXT,
                      dependencies TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ChatHistory (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      summary TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Feedback (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INT,
                      feedback TEXT)''')
    conn.commit()
    conn.close()

# Call this function when the app starts
initialize_db()

# Check if a task exists
def task_exists(title) -> bool:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Tasks WHERE title = ?", (title,))
    task = cursor.fetchone()
    conn.close()
    return task

# Get tasks
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

# Manage task
@app.post("/tasks", status_code=201)
def manage_task(task: Task):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        existing_task = task_exists(task.title)
        if existing_task:
            cursor.execute("UPDATE Tasks SET description = ?, dueDate = ?, status = ?, dependencies = ? WHERE title = ?",
                           (task.description, task.dueDate, task.status, ','.join(task.dependencies), task.title))
            task_id = existing_task[0]
        else:
            cursor.execute("INSERT INTO Tasks (title, description, dueDate, status, dependencies) VALUES (?, ?, ?, ?, ?)",
                           (task.title, task.description, task.dueDate, task.status, ','.join(task.dependencies)))
            task_id = cursor.lastrowid

        conn.commit()
        return {"task_id": task_id, "message": "Task created or updated successfully."}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Update chat history
@app.post("/chatHistory", status_code=201)
def update_chat_history(chat_history: ChatHistory):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ChatHistory (summary) VALUES (?)", (chat_history.summary,))
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Submit user feedback
@app.post("/feedback", status_code=201)
def submit_feedback(feedback: UserFeedback):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Feedback (user_id, feedback) VALUES (?, ?)", (feedback.user_id, feedback.feedback))
        conn.commit()
        feedback_id = cursor.lastrowid
        return {"feedback_id": feedback_id, "message": "Feedback submitted successfully."}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the ECO-FMM-FASTAPI v1.0"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80, reload=False)