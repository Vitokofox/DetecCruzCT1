from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import inspecciones

app = FastAPI(
    title="Grading App API",
    description="API para aplicación de gradeo",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(inspecciones.router, prefix="/api/v1", tags=["inspecciones"])

@app.get("/")
async def root():
    return {"message": "Grading App API funcionando correctamente"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)