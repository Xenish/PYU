from fastapi import APIRouter, Response

from app.observability.metrics import render_metrics

router = APIRouter()


@router.get("/metrics")
async def metrics_endpoint():
    data = render_metrics()
    return Response(content=data, media_type="text/plain; version=0.0.4")
