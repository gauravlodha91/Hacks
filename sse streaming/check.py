# # # client.py

# # import httpx

# # url = "http://127.0.0.1:8000/stream"

# # with httpx.stream("GET", url) as response:
# #     response.raise_for_status()

# #     for line in response.iter_lines():
# #         if line.startswith("data:"):
# #             data = line[5:].strip()
# #             print(data, end="", flush=True)

# # print()


# import asyncio

# import httpx


# async def main():

#     url = "http://127.0.0.1:8080/stream"

#     async with httpx.AsyncClient() as client, client.stream("GET", url) as response:
#         response.raise_for_status()

#         async for line in response.aiter_lines():
#             # if line.startswith("data:"):
#             data = line
#             print(data, end=" ", flush=True)


# asyncio.run(main())


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


if __name__ == "__main__":
    asyncio.run(main())
