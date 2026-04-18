"""
Pydantic schemas shared across all model services.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class PredictRequest(BaseModel):
    """Incoming prediction request to a model microservice."""
    input_data: str = Field(..., description="Base64-encoded media payload")
    threshold: float = Field(0.5, ge=0.0, le=1.0, description="Classification threshold")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PredictionResult(BaseModel):
    """Standardised response from every model."""
    model_name: str
    probability: float = Field(..., ge=0.0, le=1.0, description="P(fake)")
    label: str  # "fake" | "real"
    confidence: float = Field(..., ge=0.0, le=1.0)
    threshold_used: float
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @classmethod
    def build(
        cls,
        model_name: str,
        probability: float,
        threshold: float,
        extra: Optional[Dict[str, Any]] = None,
    ) -> "PredictionResult":
        label = "fake" if probability >= threshold else "real"
        # Confidence is distance from the boundary, scaled to [0,1]
        confidence = abs(probability - threshold) / max(threshold, 1 - threshold)
        confidence = min(confidence, 1.0)
        return cls(
            model_name=model_name,
            probability=round(probability, 4),
            label=label,
            confidence=round(confidence, 4),
            threshold_used=threshold,
            extra=extra or {},
        )


class HealthResponse(BaseModel):
    status: str = "ok"
    model_name: str
    model_loaded: bool
    version: str = "1.0.0"
