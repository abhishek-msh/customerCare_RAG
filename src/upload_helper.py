from docling.document_converter import DocumentConverter
import re
import tiktoken
from pymilvus import (
    CollectionSchema,
    FieldSchema,
    DataType,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.adapters.milvusmanager import milvus_manager
from src.types import MilvusVectorRecord
from src.adapters.openaimanager import openai_manager
from src.adapters.loggingmanager import logger


def count_tokens(text: str):
    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = encoding.encode(text)
    return len(tokens)


def split_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=600,
        chunk_overlap=0,
        length_function=count_tokens,
        separators=[
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ],
    )
    return text_splitter.split_text(text)


converter = DocumentConverter()


def upload_docs():
    logger.info("Starting document upload process.")
    result = converter.convert("data/Frequently-asked-questions-2022-15092022.pdf")
    logger.info("PDF converted to text.")
    pdf_text = result.document.export_to_text()
    pdf_text = re.sub(r"[^\x00-\x7F]+", " ", pdf_text)
    documentation_chunks = split_text(pdf_text)
    logger.info(f"Document split into {len(documentation_chunks)} chunks.")

    milvus_records = list(MilvusVectorRecord.model_fields.keys())
    fields = []
    fields.append(
        FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True,
            description="Unique ID for each record",
        )
    )
    for field in milvus_records:
        if field == "contentEmbeddings":
            fields.append(
                FieldSchema(
                    name=field,
                    dtype=DataType.FLOAT_VECTOR,
                    dim=1536,
                    description="Embeddings for content",
                )
            )
        else:
            fields.append(
                FieldSchema(
                    name=field,
                    dtype=DataType.VARCHAR,
                    max_length=10000,
                    description=f"Field for {field} data",
                )
            )

    logger.info("Dropping existing Milvus collection if it exists.")
    milvus_manager.milvus_client.drop_collection(
        collection_name=milvus_manager.MILVUS_COLLECTION_NAME,
    )
    schema = CollectionSchema(
        fields=fields,
        description="Collection schema for storing vectorized documents",
    )
    index_params = milvus_manager.milvus_client.prepare_index_params()
    index_params.add_index(
        field_name="contentEmbeddings",
        index_type=milvus_manager.MILVUS_INDEX_TYPE,
        metric_type=milvus_manager.MILVUS_DISTANCE_METRIC,
        index_name=milvus_manager.MILVUS_INDEX_NAME,
    )
    logger.info("Creating new Milvus collection and index.")
    milvus_manager.milvus_client.create_collection(
        collection_name=milvus_manager.MILVUS_COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )
    data_list = []
    logger.info("Generating embeddings and preparing data for insertion.")
    for idx, doc in enumerate(documentation_chunks):
        doc = doc.strip()
        temp = {
            "content": doc,
            "contentEmbeddings": openai_manager.create_embedding(doc, f"chunk_{idx}")[
                1
            ]["data"][0]["embedding"],
        }
        data_list.append(MilvusVectorRecord(**temp).model_dump())
    logger.info(f"Inserting {len(data_list)} records into Milvus.")
    res = milvus_manager.milvus_client.insert(
        collection_name=milvus_manager.MILVUS_COLLECTION_NAME,
        data=data_list,
    )

    if res["insert_count"] > 0:
        logger.info(f"Successfully inserted {res["insert_count"]} records into Milvus.")
        return f"Successfully inserted {res["insert_count"]} records into Milvus."
    else:
        logger.info("No records were inserted into Milvus.")
        return "No records were inserted into Milvus."
