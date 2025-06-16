import json
from config import SqlConfig, MilvusConfig
from src.types import (
    ChatBotModel,
    ConversationAnalyticsModel,
    UserDetailsModel,
    ComplaintModel,
)
from src.adapters.loggingmanager import logger

from src.prompts import (
    get_chatbot_prompt,
    get_complaint_status_prompt,
    get_intent_prompt,
)
from src.adapters.sqllitemanager import sql_manager
from src.adapters.openaimanager import openai_manager
from src.adapters.milvusmanager import milvus_manager
from src.utils import get_user_detail, get_complaint_status, create_complaint


class ChatBot:
    def __init__(self, data: ChatBotModel) -> None:
        self.data = data
        self.conversation_analytics = ConversationAnalyticsModel(
            **self.data.model_dump()
        )

    def get_intent(self, previous_conversations: str) -> str:
        try:
            messages = get_intent_prompt(
                user_input=self.data.user_text,
                previous_conversations=previous_conversations,
            )
            _, chat_completion_response = openai_manager.chat_completion(
                transaction_id=self.data.user_id,
                messages=messages,
            )
            intent = json.loads(
                chat_completion_response["choices"][0]["message"]["content"]
            )
            intent = intent["category"]
            logger.info(
                f"[ChatBot] - Intent detected for user_id: {self.data.user_id}, Intent: {intent}"
            )
            return intent
        except Exception as exc:
            logger.error(
                f"[ChatBot] - Error occurred while detecting intent for user_id: {self.data.user_id}, Error: {exc}"
            )
            raise exc

    def get_response(self) -> str:
        try:
            sql_query = f"""SELECT user_text, response FROM {SqlConfig().CONVERSATION_ANALYTICS_TABLE} WHERE user_id = '{self.data.user_id}' ORDER BY created_at DESC LIMIT 2;"""

            fetched_df = (
                sql_manager.fetch_data(
                    transaction_id=self.data.user_id,
                    sql_query=sql_query,
                )
                .iloc[::-1]
                .reset_index(drop=True)
            )
            previous_conversations = ""
            if not fetched_df.empty:
                for idx, row in fetched_df.iterrows():
                    previous_conversations += (
                        f"User: {row['user_text']}\nBot (You): {row['response']}\n\n"
                    )
                previous_conversations += f"User: {self.data.user_text}"
                previous_conversations = previous_conversations.strip()
            else:
                previous_conversations = "No previous conversations found."

            logger.info(
                f"[ChatBot] - Fetched previous conversations for user_id: {self.data.user_id}"
            )
            intent = self.get_intent(previous_conversations=previous_conversations)

            if intent == "status":
                logger.info(
                    f"[ChatBot] - Status request received for user_id: {self.data.user_id}"
                )
                status_messages = get_complaint_status_prompt(
                    user_input=self.data.user_text
                )
                _, chat_completion_response = openai_manager.chat_completion(
                    transaction_id=self.data.user_id,
                    messages=status_messages,
                )
                status_response = json.loads(
                    chat_completion_response["choices"][0]["message"]["content"]
                )
                logger.info(
                    f"[ChatBot] - Status response generated for user_id: {self.data.user_id}"
                )
                if status_response["followup_flag"]:

                    return status_response["followup_question"]

                result = get_complaint_status(
                    complaint_id=status_response["complaint_id"]
                )

                res = {
                    "response": "Here is the status of your complaint:",
                    "complaint_details": result,
                }
                return res

            user_details = get_user_detail(self.data.user_id)

            _, embedding_response = openai_manager.create_embedding(
                text=self.data.user_text, transaction_id=self.data.user_id
            )
            query_embedding = embedding_response["data"][0]["embedding"]
            logger.info(
                f"[ChatBot] - Embedding created for user_id: {self.data.user_id}"
            )

            _, retrieved_docs = milvus_manager.search_index(
                transaction_id=self.data.user_id,
                collection_name=MilvusConfig().MILVUS_COLLECTION_NAME,
                text_embedding=query_embedding,
                return_fields=MilvusConfig().MILVUS_RETURN_FIELDS,
                top_k=MilvusConfig().ENGLISH_MILVUS_KNN,
            )

            relevant_context = ""
            for record in retrieved_docs[0]:
                relevant_context += record.entity["content"] + "\n\n"

            if user_details is None:
                user_input = self.data.user_text
            else:
                user_info_parts = []
                if user_details.get("name"):
                    user_info_parts.append(f"I'm {user_details.get('name', '')}")
                if user_details.get("phone_number"):
                    user_info_parts.append(
                        f"my phone number is {user_details.get('phone_number', '')}"
                    )
                if user_details.get("email"):
                    user_info_parts.append(
                        f"my email is {user_details.get('email', '')}"
                    )
                user_info_str = ", ".join(user_info_parts)
                if user_info_str:
                    user_input = (
                        f"""{user_info_str}.\nComplaint/Query: {self.data.user_text}"""
                    )
                else:
                    user_input = self.data.user_text

            prompt = get_chatbot_prompt(
                user_input=user_input,
                relevant_context=relevant_context,
                past_conversations=previous_conversations,
            )
            _, chat_completion_response = openai_manager.chat_completion(
                transaction_id=self.data.user_id,
                messages=prompt,
            )
            gpt_response = json.loads(
                chat_completion_response["choices"][0]["message"]["content"]
            )
            user_info = gpt_response.get("user_info", {})
            UserDetailsModel(
                user_id=self.data.user_id,
                name=user_info.get("name", ""),
                phone_number=user_info.get("phone_number", ""),
                email=user_info.get("email", ""),
            ).to_sql()
            if gpt_response["followup_flag"]:
                self.conversation_analytics.response = gpt_response["followup_question"]
                self.conversation_analytics.followup_flag = 1
                self.conversation_analytics.complaint_details = None
                self.conversation_analytics.to_sql()
                res = {
                    "response": gpt_response["followup_question"],
                    "complaint_details": None,
                }
                return res

            self.conversation_analytics.response = gpt_response["user_info"]["response"]
            self.conversation_analytics.complaint_details = user_info[
                "complaint_details"
            ]
            self.conversation_analytics.followup_flag = 0
            self.conversation_analytics.to_sql()
            logger.info(
                f"[ChatBot] - Response generated for user_id: {self.data.user_id}"
            )
            complaint_data = create_complaint(
                ComplaintModel(
                    name=user_info["name"],
                    phone_number=user_info["phone_number"],
                    email=user_info["email"],
                    complaint_details=user_info["complaint_details"],
                )
            )
            logger.info(
                f"[ChatBot] - Complaint created for user_id: {self.data.user_id}"
            )
            res = {
                "response": self.conversation_analytics.response,
                "complaint_details": complaint_data,
            }
            return res
        except Exception as exc:
            logger.error(
                f"[ChatBot] - Error occurred for user_id: {self.data.user_id}, Error: {exc}"
            )
            raise exc
