# Server-Sent Events (SSE) — Practical & Interview Guide

## 1. What is SSE?

**Server-Sent Events (SSE)** is a standard for sending a continuous stream of events from a server to a client over a single HTTP connection.

```text
Client ───── HTTP/HTTPS request ─────► Server
Client ◄──── continuous SSE stream ─── Server
```

SSE is **one-way**:

```text
Server ─────────────────► Client
```

If you need continuous bidirectional communication, consider WebSockets.

### SSE vs HTTPS

SSE uses HTTP.

HTTPS is simply HTTP protected by TLS.

```text
SSE
 └── HTTP
      └── HTTPS = HTTP + TLS
```

Therefore this is valid:

```text
https://api.example.com/stream
```

The client still receives `text/event-stream`.

---

# 2. Core SSE Response Format

The most important SSE format is:

```text
data: Hello

```

Notice the **two newline characters**:

```python
yield "data: Hello\n\n"
```

The first `\n` terminates the line.

The second `\n` creates the blank line that tells the SSE parser:

> This event is complete.

### Event with a type

```text
event: token
data: {"text": "Hello"}

```

Python:

```python
yield (
    "event: token\n"
    'data: {"text": "Hello"}\n\n'
)
```

---

# 3. Important SSE Keywords

| Keyword | Purpose |
|---|---|
| `data:` | Event payload |
| `event:` | Event type/name |
| `id:` | Event identifier |
| `retry:` | Reconnection delay |
| `:` | SSE comment; useful for heartbeat |
| `\n\n` | Marks the end of an SSE event |
| `text/event-stream` | SSE response content type |

Example:

```text
id: 101
event: token
data: {"text": "Hello"}

```

---

# 4. Why `yield` Is Used

A normal response:

```python
return "Hello World"
```

is produced as one response.

A streaming response:

```python
async def generate():
    yield "chunk 1"
    yield "chunk 2"
    yield "chunk 3"
```

allows the server to produce data progressively.

Important distinction:

> `yield` provides HTTP response streaming. It does not automatically make the data a valid SSE event.

For SSE:

```python
yield "data: chunk 1\n\n"
```

is a complete SSE event.

---

# 5. SSE vs HTTP Streaming vs LLM Streaming

These are related but different concepts.

```text
HTTP Streaming
      │
      ▼
Transporting response chunks progressively

SSE
      │
      ▼
A standard event format over HTTP

LLM Token Streaming
      │
      ▼
The LLM produces output progressively
```

You can combine them:

```text
LLM tokens
    ↓
SSE
    ↓
HTTPS
    ↓
Frontend
```

SSE can carry much more than LLM tokens:

- Tokens
- Agent status
- Retrieval status
- Citations
- Product metadata
- Follow-up questions
- Progress events
- Errors
- Completion events

---

# 6. FastAPI — Basic SSE

FastAPI can implement SSE using Starlette's `StreamingResponse`.

No `sse-starlette` package is strictly required.

```python
import asyncio

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


async def generate():
    for message in ["Hello", "this", "is", "SSE"]:
        yield f"data: {message}\n\n"
        await asyncio.sleep(1)


@app.get("/stream")
async def stream():
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

Run:

```bash
uvicorn server:app --host 127.0.0.1 --port 8080
```

---

# 7. FastAPI Important Functions / Classes

## `FastAPI()`

Creates the FastAPI application.

```python
app = FastAPI()
```

## `@app.get()`

Creates a GET endpoint.

```python
@app.get("/stream")
async def stream():
    ...
```

## `StreamingResponse`

Streams response content progressively.

```python
return StreamingResponse(
    generator(),
    media_type="text/event-stream"
)
```

## `yield`

Produces one piece of the response.

```python
yield "data: Hello\n\n"
```

## `async def`

Useful for asynchronous streaming and I/O.

```python
async def generate():
    ...
```

## `await`

Allows asynchronous operations without blocking the event loop.

```python
await asyncio.sleep(0.1)
```

---

# 8. Do You Need `sse-starlette`?

No.

You can use:

```python
from fastapi.responses import StreamingResponse
```

and manually format SSE events.

`sse-starlette` provides:

```python
from sse_starlette.sse import EventSourceResponse
```

It is a convenience library with SSE-specific functionality.

### Simple rule

```text
FastAPI
  │
  ├── StreamingResponse
  │       └── SSE possible
  │
  └── sse-starlette
          └── dedicated SSE helper
```

For learning SSE, `StreamingResponse` is useful because it makes the underlying protocol obvious.

---

# 9. FastAPI — Structured SSE Events

For an agentic AI application, don't treat everything as plain text.

Use event types:

```text
event: token
data: {"text": "Retrieval"}

event: retrieval
data: {"documents": 5}

event: product_carousel
data: [...]

event: follow_up_questions
data: [...]

event: completed
data: {"status": "success"}
```

Example:

```python
import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


async def generate():

    yield (
        "event: status\n"
        'data: {"message": "Agent started"}\n\n'
    )

    await asyncio.sleep(1)

    yield (
        "event: token\n"
        f'data: {json.dumps({"text": "Retrieval"})}\n\n'
    )

    await asyncio.sleep(0.2)

    yield (
        "event: token\n"
        f'data: {json.dumps({"text": " Augmented"})}\n\n'
    )

    await asyncio.sleep(0.2)

    yield (
        "event: completed\n"
        'data: {"status": "success"}\n\n'
    )


@app.get("/stream")
async def stream():

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

---

# 10. Better Architecture for GenAI / Agentic AI

Keep business logic separate from transport logic.

```text
                 generate_answer()
                       │
                       │ structured events
                       ▼
                  sse_stream()
                       │
                       │ SSE formatting
                       ▼
                StreamingResponse
                       │
                       ▼
                     Client
```

The agent should not need to know about:

```text
event:
data:
\n\n
```

Those are transport concerns.

---

# 11. Example: Three-Phase GenAI Response

Suppose your application needs:

1. Initial starter line
2. Product carousel metadata
3. Follow-up questions

Business logic:

```python
import asyncio
from typing import Any


async def generate_answer(
    question: str,
    context: str,
):

    starter_line = (
        "Here are some products that I found based on your query."
    )

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
```

Then the SSE layer:

```python
import asyncio
import json


async def sse_stream(
    question: str,
    context: str,
):

    async for event_type, data in generate_answer(
        question,
        context,
    ):

        if event_type == "starter":

            for word in data.split():

                yield (
                    "event: starter\n"
                    f'data: {json.dumps({"text": word})}\n\n'
                )

                await asyncio.sleep(0.08)

        else:

            yield (
                f"event: {event_type}\n"
                f"data: {json.dumps(data)}\n\n"
            )
```

Endpoint:

```python
@app.get("/stream")
async def stream():

    return StreamingResponse(
        sse_stream(
            question="Show me some products",
            context="Shopping context",
        ),
        media_type="text/event-stream",
    )
```

---

# 12. Flask — SSE

SSE is not specific to FastAPI.

Flask can also stream SSE.

```python
from flask import Flask, Response
import time

app = Flask(__name__)


@app.route("/stream")
def stream():

    def generate():

        for message in ["Hello", "this", "is", "SSE"]:

            yield f"data: {message}\n\n"

            time.sleep(1)

    return Response(
        generate(),
        mimetype="text/event-stream",
    )


if __name__ == "__main__":
    app.run(port=8080)
```

The important Flask concept is:

```python
Response(
    generator(),
    mimetype="text/event-stream"
)
```

---

# 13. Django

Django can use `StreamingHttpResponse`.

```python
from django.http import StreamingHttpResponse
import time


def stream(request):

    def generate():

        for message in ["Hello", "this", "is", "SSE"]:

            yield f"data: {message}\n\n"

            time.sleep(1)

    return StreamingHttpResponse(
        generate(),
        content_type="text/event-stream",
    )
```

---

# 14. Python Client with `httpx`

`httpx` is not required by SSE itself.

It is simply an HTTP client that can consume the streaming response.

Install:

```bash
pip install httpx
```

Synchronous version:

```python
import httpx

url = "http://127.0.0.1:8080/stream"

with httpx.stream("GET", url) as response:

    response.raise_for_status()

    for line in response.iter_lines():

        print(line)
```

---

# 15. Async Python Client with `httpx.AsyncClient`

For async applications:

```python
import asyncio
import httpx


async def main():

    url = "http://127.0.0.1:8080/stream"

    async with httpx.AsyncClient() as client:

        async with client.stream(
            "GET",
            url,
        ) as response:

            response.raise_for_status()

            async for line in response.aiter_lines():

                print(line)


if __name__ == "__main__":
    asyncio.run(main())
```

Important mappings:

```text
Sync                         Async
------------------------------------------------
httpx.Client()               httpx.AsyncClient()

with                         async with

for                          async for

iter_lines()                 aiter_lines()
```

---

# 16. Parsing SSE on the Client

A raw SSE response looks like:

```text
event: token
data: {"text":"Hello"}

event: token
data: {"text":"world"}

event: completed
data: {"status":"success"}
```

A client can parse it:

```python
import asyncio
import json
import httpx


async def main():

    url = "http://127.0.0.1:8080/stream"

    async with httpx.AsyncClient() as client:

        async with client.stream("GET", url) as response:

            response.raise_for_status()

            event_type = None

            async for line in response.aiter_lines():

                if not line:
                    event_type = None
                    continue

                if line.startswith("event:"):
                    event_type = line[6:].strip()

                elif line.startswith("data:"):

                    data = line[5:].strip()

                    if event_type == "token":

                        payload = json.loads(data)

                        print(
                            payload["text"],
                            end=" ",
                            flush=True,
                        )

                    elif event_type == "product_carousel":

                        products = json.loads(data)

                        print("\n\nPRODUCTS:")

                        for product in products:

                            print(
                                f"- {product['name']} "
                                f"₹{product['price']}"
                            )

                    elif event_type == "follow_up_questions":

                        questions = json.loads(data)

                        print("\nFOLLOW-UP QUESTIONS:")

                        for question in questions:

                            print(f"- {question}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

# 17. Browser Client — EventSource

Browsers have a native SSE API:

```javascript
const source = new EventSource(
    "https://api.example.com/stream"
);

source.onmessage = (event) => {
    console.log(event.data);
};
```

For custom events:

```javascript
source.addEventListener("token", (event) => {
    const data = JSON.parse(event.data);

    document.getElementById("answer").textContent += data.text;
});


source.addEventListener("product_carousel", (event) => {
    const products = JSON.parse(event.data);

    renderProducts(products);
});


source.addEventListener("follow_up_questions", (event) => {
    const questions = JSON.parse(event.data);

    renderFollowUps(questions);
});
```

---

# 18. SSE and POST Requests

Native browser `EventSource` normally uses GET.

For example:

```javascript
new EventSource("/stream");
```

produces:

```text
GET /stream
```

But a GenAI request often looks like:

```text
POST /chat

{
    "question": "Explain RAG",
    "context": "..."
}
```

Two common approaches exist.

## Approach A — POST + GET stream

```text
POST /chat
     │
     ▼
job_id = 123
     │
     ▼
GET /chat/stream/123
     │
     ▼
SSE
```

## Approach B — POST + fetch streaming

The client can POST and consume the response body as a stream.

```javascript
const response = await fetch("/chat", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        question: "Explain RAG"
    })
});

const reader = response.body.getReader();

while (true) {

    const { value, done } = await reader.read();

    if (done) break;

    console.log(
        new TextDecoder().decode(value)
    );
}
```

---

# 19. Heartbeats / Keep-Alive

SSE connections can remain open for a long time.

A proxy or load balancer might close an apparently idle connection.

An SSE comment can be used as a heartbeat:

```text
: ping

```

The colon indicates an SSE comment.

The server can periodically send:

```python
yield ": ping\n\n"
```

This keeps the connection active without producing a visible application event.

For production GenAI systems, heartbeat behavior should be considered together with:

- Proxy timeout
- Load balancer timeout
- Client timeout
- Server timeout

---

# 20. Proxy / Load Balancer Buffering

This is one of the most important production concerns.

Your application might generate:

```text
token 1
token 2
token 3
token 4
```

but a proxy could buffer them and deliver them together.

```text
FastAPI
   │
   ├── token 1
   ├── token 2
   ├── token 3
   └── token 4
          │
          ▼
     Proxy buffer
          │
          ▼
       Client
```

The user then sees all tokens at once.

Therefore, verify that the production infrastructure supports streaming and does not buffer the SSE response.

This matters when deploying behind:

- Azure ingress
- Reverse proxies
- Load balancers
- API gateways
- Nginx
- CDN/proxy layers

---

# 21. HTTPS and Azure

SSE works perfectly over HTTPS.

Typical architecture:

```text
Browser
   │
   │ HTTPS
   ▼
Azure Ingress / Load Balancer
   │
   │ internal HTTP
   ▼
FastAPI container
   │
   ▼
Agent / LLM
```

The public request can be:

```text
https://api.example.com/stream
```

while the internal container communication can remain HTTP.

HTTPS provides encryption; it does not change the SSE protocol.

---

# 22. Client Disconnect / Cancellation

This is especially important for LLM and Agentic AI applications.

Example:

```text
User starts request
       ↓
Agent starts
       ↓
Retrieval
       ↓
LLM generating
       ↓
User closes browser
```

If the backend continues processing unnecessarily, you may waste:

- LLM tokens
- API calls
- compute
- tool calls

Production applications should consider detecting client disconnects and cancelling unnecessary downstream work.

---

# 23. Error Events

Don't rely only on the connection closing to indicate failure.

You can send:

```text
event: error
data: {"message":"Unable to retrieve products"}

```

Then optionally:

```text
event: completed
data: {"status":"failed"}

```

The frontend can display an appropriate error state.

---

# 24. Completion Event

A useful convention is:

```text
event: completed
data: {"status":"success"}

```

Then the client knows:

```text
started
   ↓
retrieval
   ↓
tokens
   ↓
products
   ↓
follow-ups
   ↓
completed
```

This is clearer than assuming:

> Connection closed = successful completion.

---

# 25. `id:` and Reconnection

SSE supports event IDs:

```text
id: 101
event: token
data: {"text":"Hello"}

id: 102
event: token
data: {"text":"world"}
```

Browsers can reconnect to an SSE endpoint after a connection loss.

The `Last-Event-ID` mechanism can be used to help resume from a known event.

This becomes useful for long-running or important streams.

---

# 26. Authentication

SSE is still an HTTP endpoint, so authentication/authorization can be applied.

For example:

```text
Authorization: Bearer <token>
```

However, remember that the native browser `EventSource` API has limitations around custom request headers.

For applications requiring custom authorization headers, teams often use:

- Cookie-based authentication
- A suitable SSE client library
- `fetch()` streaming
- A short-lived stream token

Don't put sensitive credentials into query parameters unless you have a deliberate security design.

---

# 27. CORS

If your frontend and backend are on different origins:

```text
Frontend:
https://app.example.com

Backend:
https://api.example.com
```

you may need CORS configuration.

FastAPI example:

```python
from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Configure CORS narrowly in production rather than blindly allowing every origin.

---

# 28. SSE vs WebSocket

| Feature | SSE | WebSocket |
|---|---|---|
| Direction | Server → Client | Bidirectional |
| Transport | HTTP | WebSocket |
| HTTPS | HTTPS | WSS |
| Browser EventSource | Yes | No |
| LLM output streaming | Excellent | Excellent |
| Agent progress events | Excellent | Excellent |
| Client continuously sending messages | No | Yes |
| Simplicity | Simple | More complex |

### Practical choice

For:

```text
User question
      ↓
Agent
      ↓
tokens/status/products
      ↓
UI
```

SSE is often a very clean choice.

For:

```text
Client ⇄ Server
continuous messages in both directions
```

consider WebSockets.

---

# 29. Important Production Headers

At minimum, your response should have:

```http
Content-Type: text/event-stream
```

Common useful headers include:

```http
Cache-Control: no-cache
Connection: keep-alive
```

With `StreamingResponse`, frameworks/proxies may manage some headers for you, but production behavior should be verified at the actual deployment layer.

---

# 30. Complete FastAPI Server

```python
import asyncio
import json
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


async def generate_answer(
    question: str,
    context: str,
):

    starter_line = (
        "Here are some products that I found based on your query."
    )

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

    follow_ups = [
        "Would you like to see similar products?",
        "Would you like me to compare these products?",
        "Would you like recommendations under ₹1000?",
    ]

    yield "starter", starter_line

    await asyncio.sleep(1)

    yield "product_carousel", products

    await asyncio.sleep(1)

    yield "follow_up_questions", follow_ups


async def sse_stream(
    question: str,
    context: str,
):

    try:

        async for event_type, data in generate_answer(
            question,
            context,
        ):

            if event_type == "starter":

                for word in data.split():

                    yield (
                        "event: token\n"
                        f'data: {json.dumps({"text": word})}\n\n'
                    )

                    await asyncio.sleep(0.08)

            else:

                yield (
                    f"event: {event_type}\n"
                    f"data: {json.dumps(data)}\n\n"
                )

        yield (
            "event: completed\n"
            'data: {"status":"success"}\n\n'
        )

    except Exception as exc:

        yield (
            "event: error\n"
            f'data: {json.dumps({"message": str(exc)})}\n\n'
        )


@app.get("/stream")
async def stream():

    return StreamingResponse(
        sse_stream(
            question="Show me products",
            context="Previous conversation",
        ),
        media_type="text/event-stream",
    )
```

Run:

```bash
uvicorn server:app --host 127.0.0.1 --port 8080
```

---

# 31. Complete Python Client

```python
import asyncio
import json

import httpx


async def main():

    url = "http://127.0.0.1:8080/stream"

    async with httpx.AsyncClient() as client:

        async with client.stream(
            "GET",
            url,
        ) as response:

            response.raise_for_status()

            event_type = None

            async for line in response.aiter_lines():

                if not line:
                    event_type = None
                    continue

                if line.startswith("event:"):

                    event_type = line[6:].strip()

                elif line.startswith("data:"):

                    payload = json.loads(
                        line[5:].strip()
                    )

                    if event_type == "token":

                        print(
                            payload["text"],
                            end=" ",
                            flush=True,
                        )

                    elif event_type == "product_carousel":

                        print("\n\nPRODUCT CAROUSEL")

                        for product in payload:

                            print(
                                f"{product['name']} - "
                                f"₹{product['price']}"
                            )

                    elif event_type == "follow_up_questions":

                        print("\n\nFOLLOW-UP QUESTIONS")

                        for question in payload:

                            print(f"- {question}")

                    elif event_type == "completed":

                        print("\n\nStream completed.")

                    elif event_type == "error":

                        print(
                            f"\nERROR: "
                            f"{payload['message']}"
                        )


if __name__ == "__main__":
    asyncio.run(main())
```

---

# 32. Quick `curl` Test

SSE can also be tested without a UI.

```bash
curl -N \
  -H "Accept: text/event-stream" \
  http://127.0.0.1:8080/stream
```

`-N` disables curl buffering so chunks are displayed progressively.

---

# 33. Interview Questions and Answers

## Q1. What is SSE?

> SSE is a standard for server-to-client streaming over HTTP. The server keeps an HTTP connection open and sends events progressively using the `text/event-stream` content type.

## Q2. Is SSE based on HTTP?

> Yes. SSE uses a persistent HTTP connection. HTTPS can be used to encrypt that HTTP connection.

## Q3. Is SSE bidirectional?

> No. SSE is primarily server-to-client. For bidirectional communication, WebSockets are more appropriate.

## Q4. Why do we use `text/event-stream`?

> It tells the client that the response is an SSE stream rather than a normal JSON or HTML response.

## Q5. Why do we use `\n\n`?

> SSE uses a blank line to mark the end of an event. Therefore `data: hello\n\n` represents a complete SSE event.

## Q6. Does `yield` itself mean SSE?

> No. `yield` enables incremental response generation. SSE additionally requires the response to use the SSE format, such as `data:` and event boundaries.

## Q7. Does SSE require FastAPI?

> No. SSE is a web standard. FastAPI, Flask, Django, Node.js and other frameworks can implement it.

## Q8. Does SSE require `sse-starlette`?

> No. FastAPI/Starlette's `StreamingResponse` can implement SSE directly. `sse-starlette` provides a dedicated SSE response implementation and additional conveniences.

## Q9. Can SSE use HTTPS?

> Yes. SSE can run over HTTPS exactly like other HTTP traffic.

## Q10. How does SSE help LLM applications?

> The LLM or agent produces output progressively, and SSE can transport tokens, agent status, retrieval results, tool events, citations and structured UI metadata to the frontend in real time.

## Q11. What happens if a proxy buffers the response?

> The client may receive multiple generated events together instead of progressively. Therefore streaming/buffering behavior must be configured and tested across the complete production network path.

## Q12. What happens if the connection drops?

> SSE clients can reconnect. Event IDs and `Last-Event-ID` can be used to support resuming from a known event.

## Q13. How do you keep a long SSE connection alive?

> Use heartbeats/keep-alive events and configure appropriate client, proxy, load-balancer and server timeouts.

## Q14. SSE vs WebSocket?

> SSE is simpler and well suited for server-to-client streaming such as LLM responses. WebSockets provide full bidirectional communication and are better when both client and server need continuous real-time messaging.

## Q15. Can browser `EventSource` send a POST request?

> Native `EventSource` is designed around GET. If a streaming POST is required, `fetch()` with a readable response stream is a common alternative.

---

# 34. Most Important Interview Mental Model

Remember this:

```text
                SSE
                 │
                 ▼
        HTTP streaming format
                 │
                 ▼
        text/event-stream
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
     token     status    metadata
       │         │         │
       └─────────┼─────────┘
                 ▼
               Client
```

For GenAI:

```text
LLM / Agent
     │
     ├── token
     ├── retrieval status
     ├── tool status
     ├── citation
     ├── product metadata
     ├── follow-up questions
     └── completed
             │
             ▼
            SSE
             │
             ▼
          Frontend
```

### The one-line interview answer

> **"SSE is an HTTP-based, server-to-client streaming mechanism where the server keeps the connection open and sends structured `text/event-stream` events progressively. In GenAI systems, it can stream LLM tokens as well as agent status and structured UI events such as citations, products and follow-up questions."**

---

# 35. Final Checklist

Before deploying SSE, verify:

- [ ] Response uses `text/event-stream`
- [ ] Events use correct SSE formatting
- [ ] Events end with `\n\n`
- [ ] Proxy/load-balancer buffering is handled
- [ ] Idle/read timeouts are appropriate
- [ ] Heartbeats are considered for long-running streams
- [ ] Client disconnect/cancellation is handled
- [ ] Errors are represented clearly
- [ ] Completion event is defined
- [ ] Authentication is implemented appropriately
- [ ] CORS is configured if frontend/backend are on different origins
- [ ] HTTPS is enabled in production
- [ ] Reconnection/resume is considered for important long-running streams
- [ ] LLM token generation is separated from SSE transport logic

---

# 36. Recommended Architecture

For an enterprise GenAI application:

```text
                         HTTPS
                           │
                           ▼
                    ┌─────────────┐
                    │  Frontend   │
                    └──────┬──────┘
                           │
                    POST /chat
                           │
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Agent / LangGraph│
                  └────────┬────────┘
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
             Retrieval   Tools       LLM
                │          │          │
                └──────────┼──────────┘
                           │
                           ▼
                      SSE Layer
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
             Tokens     Metadata    Status
                │          │          │
                └──────────┼──────────┘
                           ▼
                        Frontend
```

The key architectural principle is:

> **Business/agent logic generates events. The SSE layer transports those events. The frontend renders them.**

