from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Astroloh API",
    description="Астрологическое API",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Astroloh API работает!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Сервер работает"}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API endpoint работает корректно"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)