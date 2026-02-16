"""
数独求解后端 API 入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import sudoku

app = FastAPI(
    title="数独求解 API",
    description="提供数独求解、校验等接口",
    version="0.1.0",
)

# CORS：方便前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sudoku.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "数独求解 API", "docs": "/docs"}
