from pydantic import BaseModel, Field

class ValidationResult(BaseModel):
    """填数谜题合法性校验结果"""
    valid: bool = Field(..., description="当前棋盘是否符合规则")
    message: str = Field(default="", description="校验说明")