import asyncio
import json
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


import asyncio
import json
from typing import Any


async def generate_answer(
    question: str,
    context: str,
):
    starter_line = "Here are some products that I found based on your query."

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

    follow_up_questions = [
        "Would you like to see similar products?",
        "Would you like me to compare these products?",
        "Would you like recommendations under ₹1000?",
    ]

    yield "starter", starter_line

    await asyncio.sleep(3)

    yield "product_carousel", products

    await asyncio.sleep(3)

    yield "follow_up_questions", follow_up_questions


async def sse_stream(question: str, context: str):

    async for event_type, data in generate_answer(question, context):
        if event_type == "starter":
            for word in data.split():
                yield (f"event: starter\ndata: {json.dumps({'text': word})}\n\n")

                await asyncio.sleep(0.08)

        else:
            yield (f"event: {event_type}\ndata: {json.dumps(data)}\n\n")


@app.get("/stream")
async def stream():

    return StreamingResponse(
        sse_stream(
            question="Show me some products",
            context="Shopping context",
        ),
        media_type="text/event-stream",
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
