from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from src.types import ComplaintModel, ChatBotModel
from src.upload_helper import upload_docs
from src.utils import generate_complaint, get_complaint_client, create_sql_tables
from src.bot import ChatBot
from dotenv import load_dotenv

load_dotenv(override=True)

create_sql_tables()

app = FastAPI(
    title="Cyfuture AI Bot",
    description=(
        "Cyfuture AI Bot provides endpoints for managing chatbot conversations,"
    ),
)

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def read_root():
    return {"Response": "Welcome to the Cyfuture AI Bot!"}


@app.post("/upload_docs", tags=["Upload"])
def upload_documents():
    res = {"message": upload_docs()}
    return res


@app.get("/complaints/{complaint_id}", tags=["Complaints"])
def get_complaint(complaint_id: str):
    _, complaint = get_complaint_client(complaint_id)
    return complaint


@app.post("/complaints", tags=["Complaints"])
def create_complaint(data: ComplaintModel):
    _, complaint_analytics = generate_complaint(data)
    return {
        "complaint_id": complaint_analytics.complaint_id,
        "message": "Complaint created successfully",
    }


@app.post("/chatbot", tags=["ChatBot"])
def chatbot_interaction(data: ChatBotModel):
    chatbot_obj = ChatBot(data)
    response = chatbot_obj.get_response()
    return {"bot_response": response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8083)
