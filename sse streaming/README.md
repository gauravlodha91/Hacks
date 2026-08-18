version 1::

import asyncio
import json
from typing import Any

async def generate_answer(
question: str,
context: str,
):
"""
Business/agent logic.
Produces the content that needs to be streamed.
"""

    # 1. Initial starter line
    starter_line = (
        "Here are some products that I found based on your query."
    )

    # 2. Product carousel metadata
    products: list[dict[str, Any]] = [
        {
            "id": "P001",
            "name": "Product A",
            "price": 999,
            "image": "https://example.com/product-a.jpg",
        },
        {
            "id": "P002",
            "name": "Product B",
            "price": 1299,
            "image": "https://example.com/product-b.jpg",
        },
        {
            "id": "P003",
            "name": "Product C",
            "price": 1499,
            "image": "https://example.com/product-c.jpg",
        },
    ]

    # 3. Follow-up questions
    follow_up_questions = [
        "Would you like to see similar products?",
        "Would you like me to compare these products?",
        "Would you like recommendations under ₹1000?",
    ]

    # Generator only passes messages/events
    yield {
        "type": "starter",
        "data": starter_line,
    }

    yield {
        "type": "product_carousel",
        "data": products,
    }

    yield {
        "type": "follow_up_questions",
        "data": follow_up_questions,
    }

async def stream_message(message):

    message_type = message["type"]
    data = message["data"]

    if message_type == "starter":

        for word in data.split():
            yield (
                "event: starter\n"
                f"data: {json.dumps({'text': word})}\n\n"
            )

            await asyncio.sleep(0.08)

    elif message_type == "product_carousel":

        yield (
            "event: product_carousel\n"
            f"data: {json.dumps(data)}\n\n"
        )

    elif message_type == "follow_up_questions":

        yield (
            "event: follow_up_questions\n"
            f"data: {json.dumps(data)}\n\n"
        )

async def generate_stream(question: str, context: str):

    async for message in generate_answer(question, context):

        async for event in stream_message(message):

            yield event

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/stream")
async def stream():

    return StreamingResponse(
        generate_stream(
            question="Show me some products",
            context="Shopping context",
        ),
        media_type="text/event-stream",
    )

# # # client.py

# # import httpx

# # url = "http://127.0.0.1:8000/stream"

# # with httpx.stream("GET", url) as response:

# # response.raise_for_status()

# # for line in response.iter_lines():

# # if line.startswith("data:"):

# # data = line[5:].strip()

# # print(data, end="", flush=True)

# # print()

# import asyncio

# import httpx

# async def main():

# url = "http://127.0.0.1:8080/stream"

# async with httpx.AsyncClient() as client, client.stream("GET", url) as response:

# response.raise_for_status()

# async for line in response.aiter_lines():

# # if line.startswith("data:"):

# data = line

# print(data, end=" ", flush=True)

# asyncio.run(main())

check.py

import asyncio
import json

import httpx

async def main():

    url = "http://127.0.0.1:8080/stream"

    async with httpx.AsyncClient() as client, client.stream("GET", url) as response:
        response.raise_for_status()

        event_type = None

        async for line in response.aiter_lines():
            if not line:
                # Blank line = SSE event completed
                event_type = None
                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()

            elif line.startswith("data:"):
                data = line[5:].strip()

                if event_type == "starter":
                    payload = json.loads(data)
                    print(payload["text"], end=" ", flush=True)

                elif event_type == "product_carousel":
                    products = json.loads(data)

                    print("\n\nPRODUCTS:")
                    for product in products:
                        print(f"{product}")

                elif event_type == "follow_up_questions":
                    questions = json.loads(data)

                    print("\nFOLLOW-UP QUESTIONS:")
                    for question in questions:
                        print(f"- {question}")

if **name** == "**main**":
asyncio.run(main())
