"""
数独求解后端 API 入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.puzzles  # noqa: F401 — 触发 PuzzleRegistry 注册
from app.api.routes import puzzle

app = FastAPI(
    title="谜题求解 API",
    description="提供数独等谜题的求解、校验接口",
    version="0.2.0",
)

# CORS：方便前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(puzzle.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "数独求解 API", "docs": "/docs"}
