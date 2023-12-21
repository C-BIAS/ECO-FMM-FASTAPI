from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
from contextlib import contextmanager
from fastapi import Query


app = FastAPI()

class Task(BaseModel):
    id: Optional[int] = Field(None, description="Unique ID of the task")
    title: str
    description: str
    due_date: str
    status: str
    priority: int = Field(ge=1, le=5)
    status: str = Field(..., description="Status of the task, can be used to specify 'Behavioral Prompt'")

class UserFeedback(BaseModel):
    user_id: int
    feedback: str

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('tasks.db')
    try:
        yield conn
    finally:
        conn.close()

def initialize_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL,
                      description TEXT NOT NULL,
                      due_date TEXT NOT NULL,
                      status TEXT NOT NULL,
                      priority INTEGER NOT NULL CHECK (priority >= 1 AND priority <= 5))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Feedback (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      feedback TEXT NOT NULL)''')
        conn.commit()

def check_db_exists():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='Tasks' OR name='Feedback')")
            return len(cursor.fetchall()) == 2
    except Exception as e:
        print(f"Error checking if DB exists: {e}")
        return False

if not check_db_exists():
    initialize_db()
    print("Database and tables are created.")

def task_exists(task_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Tasks WHERE id = ?", (task_id,))
        return cursor.fetchone() is not None

@app.get("/tasks")
def get_tasks(category: Optional[str] = Query(None, alias="category")):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM Tasks"
            params = ()
            if category:
                query += " WHERE status = ?"
                params = (category,)
            print(f"Executing query: {query} with params: {params}")  # Debug print statement
            cursor.execute(query, params)
            tasks = cursor.fetchall()
            if not tasks:
                print(f"No tasks found with category '{category}'")  # Debug print statement
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, task)) for task in tasks]
    except Exception as e:
        print(f"Failed to retrieve tasks: {str(e)}")  # Debug print statement
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")


@app.post("/tasks", status_code=201)
def manage_task(task: Task):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if task.id and task_exists(task.id):
                cursor.execute("UPDATE Tasks SET title = ?, description = ?, due_date = ?, status = ?, priority = ? WHERE id = ?",
                               (task.title, task.description, task.due_date, task.status, task.priority, task.id))
                return {"task_id": task.id, "message": "Task updated successfully."}
            else:
                cursor.execute("INSERT INTO Tasks (title, description, due_date, status, priority) VALUES (?, ?, ?, ?, ?)",
                               (task.title, task.description, task.due_date, task.status, task.priority))
                task_id = cursor.lastrowid
                conn.commit()  # Make sure to commit the changes
                return {"task_id": task_id, "message": "Task created successfully."}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="Database integrity error: Task could not be managed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/feedback", status_code=201)
def submit_feedback(feedback: UserFeedback):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Feedback (user_id, feedback) VALUES (?, ?)", 
                           (feedback.user_id, feedback.feedback))
            feedback_id = cursor.lastrowid
            return {"feedback_id": feedback_id, "message": "Feedback submitted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@app.get("/")
def read_root():
  return {"message": "Welcome to the ECO-FMM-FASTAPI v1.4.0 API!"}
  
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80, reload=False)
