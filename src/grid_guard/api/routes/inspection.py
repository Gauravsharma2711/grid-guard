"""Inspection ticket generation and prioritized work order queue routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from grid_guard.api.dependencies import get_inference_service
from grid_guard.api.schemas.inspection import (
    InspectionQueueRequest,
    InspectionQueueResponse,
    InspectionTicketResponse,
)
from grid_guard.api.schemas.prediction import SingleMeterPredictionRequest
from grid_guard.api.services.inference import InferenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/inspection", tags=["Inspection & Field Dispatch"])


@router.post(
    "/ticket",
    response_model=InspectionTicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Field Inspection Work Order Ticket",
    description=(
        "Evaluates the target meter and compiles a complete, actionable field inspection ticket. "
        "Includes deterministic ticket ID, probability risk, estimated recoverable revenue, dispatch cost, "
        "Expected Net Value (ENV), active threshold, detected electrical tampering signatures, and audited human-readable narratives."
    ),
    responses={
        200: {"description": "Inspection ticket generated successfully"},
        400: {"description": "Insufficient history or invalid meter payload"},
        422: {"description": "Pydantic validation failure"},
        503: {"description": "Model service unavailable"},
    },
)
async def generate_inspection_ticket(
    request: SingleMeterPredictionRequest,
    service: InferenceService = Depends(get_inference_service),
) -> InspectionTicketResponse:
    """Generate an inspection ticket with full explainability evidence."""
    try:
        return service.generate_ticket(request)
    except ValueError as e:
        logger.warning(f"Validation error generating ticket for '{request.meter_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            f"Internal error generating ticket for '{request.meter_id}': {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ticket generation failed: {type(e).__name__}",
        ) from e


@router.post(
    "/queue",
    response_model=InspectionQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Prioritized Field Inspection Queue",
    description=(
        "Retrieves and filters candidate inspection tickets ranked strictly by Expected Net Value (ENV) descending. "
        "Allows dynamic filtering by minimum ENV threshold, minimum probability cutoff, and maximum crew capacity limit."
    ),
    responses={
        200: {"description": "Ranked inspection queue returned successfully"},
        404: {"description": "Precomputed evaluation artifacts not found"},
        503: {"description": "Model service unavailable"},
    },
)
async def get_inspection_queue(
    request: InspectionQueueRequest,
    service: InferenceService = Depends(get_inference_service),
) -> InspectionQueueResponse:
    """Query prioritized inspection queue."""
    try:
        return service.get_inspection_queue(request)
    except FileNotFoundError as e:
        logger.warning(f"Inspection queue artifacts missing: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Internal error querying inspection queue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Queue query failed: {type(e).__name__}",
        ) from e
