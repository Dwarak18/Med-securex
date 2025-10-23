# backend_multi.py
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
import uvicorn
import sys

app = FastAPI()

@app.post("/submit")
async def submit(data: dict):
    return {"service": "default", "message": "Request reached backend /submit", "data": data}

@app.post("/auth/login")
async def auth_login(body: dict):
    return {"service": "auth", "path": "/auth/login", "body": body}

@app.post("/users")
async def users_create(body: dict):
    return {"service": "users", "path": "/users", "body": body}

@app.get("/users/{user_id}")
async def users_get(user_id: int):
    return {"service": "users", "path": f"/users/{user_id}", "user_id": user_id}

@app.post("/orders")
async def orders_create(body: dict):
    return {"service": "orders", "path": "/orders", "body": body}

@app.get("/orders/{order_id}")
async def orders_get(order_id: int):
    return {"service": "orders", "path": f"/orders/{order_id}", "order_id": order_id}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "backend"}


# Convenience endpoint to trigger Nginx internal file serving via X-Accel-Redirect.
# Nginx must be configured with an internal location (/_internal_static/) pointing
# to the directory that contains `index.html`. When this endpoint is proxied
# through Nginx, Nginx will serve the internal file.
@app.get("/serve_index")
async def serve_index():
    # In a production setup the backend would only return this header for
    # approved/benign requests. Nginx will intercept the header and serve the
    # internal file configured at /_internal_static/index.html.
    return Response(status_code=200, headers={"X-Accel-Redirect": "/_internal_static/index.html"})


# Local testing endpoint: return the index.html file directly from the workspace.
# This is useful when testing the backend/gateway without running Nginx.
@app.get("/local_index")
async def local_index():
    # Adjust path if you run the backend from a different working directory.
    local_path = "/workspaces/codespaces-blank/index.html"
    return FileResponse(local_path, media_type="text/html")

if __name__ == "__main__":
    port = 9000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    uvicorn.run("backend:app", host="0.0.0.0", port=port, reload=True)
