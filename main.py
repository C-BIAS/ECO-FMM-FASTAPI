@app.get("/logs")
def read_logs():
    try:
        with open('database_actions.log', 'r') as file:
            log_contents = file.read()
        return {"log_contents": log_contents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from datetime import datetime 
import sqlite3
from contextlib import contextmanager
from fastapi import Query
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Set up logger to write to file with the appropriate format
logging.basicConfig(filename='database_actions.log',
                    filemode='a', # Append to the log file if it exists
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s')
def log_action(action: str):
  logging.info(action)


app = FastAPI()
security = HTTPBearer()
SECRET_TOKEN = os.getenv('SECRET_TOKEN')

def verify_token(auth_credentials: HTTPAuthorizationCredentials = Depends(security)):
    if auth_credentials.credentials != SECRET_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized access, invalid token"
        )

class Task(BaseModel):
    id: Optional[int] = Field(None, description="Unique ID of the task")
    title: str
    description: str
    due_date: Optional[str] = Field(None, description="Due date of the task in DD-MM-YYYY format")
    status: str = Field(..., description="Status of the task, can be used to specify 'Behavioral Prompt'")
    priority: int = Field(ge=1, le=5)
    area: Optional[str] = Field(None, description="The area of the task: personal, work, project development, custom area")

@classmethod
def parse_due_date(cls, due_date: str):
    if due_date is None:
        return due_date
    try:
        return datetime.strptime(due_date, '%d-%m-%Y')
    except ValueError:
        raise ValueError('due_date must be in the format DD-MM-YYYY')

def __init__(__pydantic_self__, **data):
    if 'due_date' in data:
        data['due_date'] =__pydantic_self__.parse_due_date(data['due_date'])
    super().__init__(**data)


class UserFeedback(BaseModel):
    user_id: int
    feedback: str

class Behavior(BaseModel):
    id: Optional[int] = Field(None, description="Unique ID of the behavior")
    description: str
  

@contextmanager
def get_db_connection(database: str):
    log_action(f'Connecting to database: {database}')
    conn = sqlite3.connect(f'{database}.sqlite')
    try:
        yield conn
    finally:
        conn.close()
        log_action(f'Disconnected from database: {database}')

def initialize_databases():
    # Initialize tasks_db.sqlite
    with get_db_connection("tasks_db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL CHECK (priority >= 1 AND priority <= 5),
                area TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                feedback TEXT NOT NULL
            )
        ''')
        conn.commit()

    # Initialize behavior_db.sqlite
    with get_db_connection("behavior_db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL
            )
        ''')
        conn.commit()

initialize_databases() # Call the function to initialize both databases

def task_exists(task_id: int, database: str = "tasks_db") -> bool:
    with get_db_connection(database) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Tasks WHERE id = ?", (task_id,))
        return cursor.fetchone() is not None

@app.post("/tasks", status_code=201, dependencies=[Depends(verify_token)])
def manage_task(task: Task):
    try:
        with get_db_connection("tasks_db") as conn:
            cursor = conn.cursor()
            if task.id and task_exists(task.id):
                cursor.execute(
                    "UPDATE Tasks SET title = ?, description = ?, due_date = ?, status = ?, priority = ?, area = ? WHERE id = ?",
                    (task.title, task.description, task.due_date, task.status, task.priority, task.area, task.id)
                )
                task_id = task.id  # Assign the task ID after updating
                log_action(f"Updated Task with ID {task_id}")
            else:
                cursor.execute(
                    "INSERT INTO Tasks (title, description, due_date, status, priority, area) VALUES (?, ?, ?, ?, ?, ?)",
                    (task.title, task.description, task.due_date, task.status, task.priority, task.area)
                )
                task_id = cursor.lastrowid  # Assign the task ID after insertion
                log_action(f"Inserted new Task with ID {task_id}")
            conn.commit()
            return {"task_id": task_id, "message": "Task created or updated successfully."}  # Use task_id after it's been assigned in both conditions
    except sqlite3.IntegrityError as e:
        log_action(f"Database integrity error: Task could not be managed. Error: {e}")
        raise HTTPException(status_code=400, detail="Database integrity error: Task could not be managed.")
    except Exception as e:
        log_action(f"Server error: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/tasks", dependencies=[Depends(verify_token)])
def get_tasks():
    try:
        with get_db_connection("tasks_db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Tasks")
            tasks = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, task)) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")
      
@app.get("/tasks/{task_id}", dependencies=[Depends(verify_token)])
def get_task_by_id(task_id: int):
    try:
        with get_db_connection("tasks_db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            if task:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, task))
            else:
                raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")
      
@app.post("/feedback", status_code=201, dependencies=[Depends(verify_token)])
def submit_feedback(feedback: UserFeedback):
    log_action(f"Feedback submission endpoint called with feedback: {feedback.json()}")
    try:
        with get_db_connection("tasks_db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Feedback (user_id, feedback) VALUES (?, ?)", 
                           (feedback.user_id, feedback.feedback))
            feedback_id = cursor.lastrowid
            conn.commit()
        log_action(f"Feedback with ID {feedback_id} submitted successfully")
        return {"feedback_id": feedback_id, "message": "Feedback submitted successfully."}
    except Exception as e:
        log_action(f"Failed to submit feedback: {e}", level=logging.ERROR)
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@app.post("/behaviors", status_code=201, dependencies=[Depends(verify_token)])
def add_behavior(behavior: Behavior):
    log_action(f"Add behavior endpoint called with behavior: {behavior.json()}")
    try:
        with get_db_connection("behavior_db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Behavior (description) VALUES (?)", 
                           (behavior.description,))
            behavior_id = cursor.lastrowid
            conn.commit()
        log_action(f"Behavior with ID {behavior_id} added successfully")
        return {"behavior_id": behavior_id, "message": "Behavior added successfully."}
    except Exception as e:
        log_action(f"Failed to add behavior: {e}", level=logging.ERROR)
        raise HTTPException(status_code=500, detail=f"Failed to add behavior: {str(e)}")


@app.get("/behaviors", dependencies=[Depends(verify_token)])
def get_behaviors():
    try:
        with get_db_connection("behavior_db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Behavior")
            behaviors = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, behavior)) for behavior in behaviors]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve behaviors: {str(e)}")

@app.get("/logs")
def read_logs():
    try:
        with open('database_actions.log', 'r') as file:
            log_contents = file.read()
        return {"log_contents": log_contents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")

@app.get("/")
def read_root():
  return {"message": "Welcome to the ECO-FMM-FASTAPI v2.1.0 API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80, reload=False)