"""Inference and prediction routes for single-meter and multi-meter batches."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from grid_guard.api.dependencies import get_inference_service
from grid_guard.api.schemas.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    SingleMeterPredictionRequest,
    SingleMeterPredictionResponse,
)
from grid_guard.api.services.inference import InferenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/predict", tags=["Inference & Prediction"])


@router.post(
    "",
    response_model=SingleMeterPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Single Smart Meter",
    description=(
        "Ingests a raw daily smart-meter time series, calculates 60 canonical temporal features, "
        "scores the meter with the cost-sensitive LightGBM champion booster, evaluates financial exposure "
        "and Expected Net Value (ENV), and optionally computes Tree-SHAP local attributions and domain tampering narratives."
    ),
    responses={
        200: {"description": "Successful inference and decision response"},
        400: {"description": "Insufficient history or malformed input readings"},
        422: {"description": "Pydantic validation failure"},
        503: {"description": "Model service unavailable"},
    },
)
async def predict_single_meter(
    request: SingleMeterPredictionRequest,
    service: InferenceService = Depends(get_inference_service),
) -> SingleMeterPredictionResponse:
    """Evaluate an individual meter's recent consumption time series."""
    try:
        return service.predict_single(request)
    except ValueError as e:
        logger.warning(f"Validation error in single meter prediction for '{request.meter_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Internal error processing meter '{request.meter_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected internal error occurred during inference: {type(e).__name__}",
        ) from e


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Batch of Smart Meters",
    description=(
        "Synchronously processes a bounded batch of smart-meter requests (up to configured maximum, e.g. 50 meters). "
        "Supports partial success: valid meters return predictions while malformed meters return structured per-item error records."
    ),
    responses={
        200: {"description": "Batch processing completed with item-level results and errors"},
        400: {"description": "Batch size exceeds configured maximum"},
        422: {"description": "Batch schema validation failure"},
        503: {"description": "Model service unavailable"},
    },
)
async def predict_batch_meters(
    request: BatchPredictionRequest,
    service: InferenceService = Depends(get_inference_service),
) -> BatchPredictionResponse:
    """Evaluate a bounded batch of meter histories."""
    try:
        return service.predict_batch(request)
    except ValueError as e:
        logger.warning(f"Batch validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Internal error processing batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch execution failed: {type(e).__name__}",
        ) from e
