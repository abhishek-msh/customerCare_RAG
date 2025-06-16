import uuid
import requests
from src.adapters.sqllitemanager import sql_manager

from src.adapters.loggingmanager import logger
from src.types import ComplaintModel, ComplaintAnalyticsModel
from src.decorators import measure_time
from config import SqlConfig


@measure_time
def generate_complaint(complaint: ComplaintModel):
    complaint_analytics = ComplaintAnalyticsModel(**complaint.model_dump())
    complaint_analytics.complaint_id = str(uuid.uuid4())
    complaint_analytics.status = "Pending"
    try:
        complaint_analytics.to_sql()
        logger.info(
            f"[generate_complaint] - Complaint {complaint_analytics.complaint_id} generated successfully"
        )
        return complaint_analytics
    except Exception as e:
        logger.exception(f"[generate_complaint] - Error generating complaint: {str(e)}")
        raise e


@measure_time
def get_complaint_client(complaint_id: str) -> ComplaintAnalyticsModel:
    try:
        query = f"SELECT * FROM {SqlConfig().COMPLAINTS_TABLE} WHERE complaint_id = '{complaint_id}';"
        result = sql_manager.fetch_data(transaction_id=complaint_id, sql_query=query)
        if result.empty:
            logger.info(
                f"[get_complaint_client] - No complaint found for ID: {complaint_id}"
            )
            return ComplaintAnalyticsModel(
                name="Unknown",
                phone_number="Unknown",
                email="Unknown",
                complaint_id=complaint_id,
                status="Not Found",
                complaint_details="No details available for this complaint ID.",
            )
        row = result.iloc[0].to_dict()
        return ComplaintAnalyticsModel(**row)
    except Exception as e:
        logger.exception(
            f"[get_complaint_client] - Error fetching complaint for ID {complaint_id}: {str(e)}"
        )
        raise e


def get_user_detail(user_id: str):
    """
    Fetches the most recent user details for a given user ID from the database.

    Args:
        user_id (str): The unique identifier of the user whose details are to be retrieved.

    Returns:
        dict: A dictionary containing the user's name, phone number, and email if found;
              otherwise, an empty dictionary.

    Logs:
        Issues a warning if no user details are found for the given user ID.
    """
    query = f"SELECT * FROM {SqlConfig().USER_DETAILS_TABLE} WHERE user_id = '{user_id}' ORDER BY created_at DESC LIMIT 1;"
    result = (
        sql_manager.fetch_data(transaction_id=user_id, sql_query=query)
        .iloc[::-1]
        .reset_index(drop=True)
    )
    if not result.empty:
        logger.info(f"[get_user_detail] - User details fetched for {user_id}")
        return result.iloc[0].to_dict()
    else:
        logger.info(f"[get_user_detail] - No user details found for {user_id}")
        return None


def get_complaint_status(complaint_id: str) -> dict:
    """
    Fetches the status of a complaint based on its ID.

    Args:
        complaint_id (str): The unique identifier of the complaint.

    Returns:
        dict: A dictionary containing the status of the complaint.
    """
    # Fetch details via the GET /complaints/{complaint_id} endpoint.
    url = f"http://localhost:8083/complaints/{complaint_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        complaint_data = response.json()
        return complaint_data
    except requests.RequestException as e:
        logger.exception(
            f"[get_complaint_status] - Error fetching complaint status for {complaint_id}: {str(e)}"
        )
        raise e


def create_complaint(complaint: ComplaintModel) -> ComplaintAnalyticsModel:
    """
    Creates a new complaint and returns the complaint analytics model.

    Args:
        complaint (ComplaintModel): The complaint model containing the details of the complaint.

    Returns:
        ComplaintAnalyticsModel: The created complaint analytics model.
    """
    url = "http://localhost:8083/complaints"
    try:
        response = requests.post(url, json=complaint.model_dump())
        response.raise_for_status()
        complaint_data = response.json()
        return complaint_data
    except requests.RequestException as e:
        logger.exception(f"[create_complaint] - Error creating complaint: {str(e)}")
        raise e


def create_sql_tables():
    try:
        complaint_table_schema = """
CREATE TABLE IF NOT EXISTS cyfuture_complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id TEXT NOT NULL,
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    email TEXT NOT NULL,
    complaint_details TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
    """
        sql_manager.execute_query("test", complaint_table_schema)

        user_table_schema = """CREATE TABLE IF NOT EXISTS cyfuture_user_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
        sql_manager.execute_query("test", user_table_schema)

        conversation_analytics_table_schema = """CREATE TABLE IF NOT EXISTS cyfuture_conversation_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    user_text TEXT NOT NULL,
    complaint_details TEXT,
    response TEXT NOT NULL,
    followup_flag INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

        sql_manager.execute_query("test", conversation_analytics_table_schema)
        logger.info("[create_sql_tables] - SQL tables created successfully")

        return True
    except Exception as e:
        logger.exception(f"[create_sql_tables] - Error creating SQL tables: {str(e)}")
        raise e
