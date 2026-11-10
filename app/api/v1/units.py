from typing import Literal, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import BranchContext, get_branch_context, get_unit_service
from app.models.unit import UnitType
from app.schemas.common import Page
from app.schemas.unit import (
    UnitCreate,
    UnitListQuery,
    UnitOut,
    UnitUpdate,
)
from app.services.unit_service import UnitService

router = APIRouter(prefix="/units", tags=["Units"])


@router.post(
    "",
    response_model=UnitOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create unit",
    description="Create a new measurement unit for the current branch.",
)
async def create_unit(
    unit_in: UnitCreate,
    branch_ctx: BranchContext = Depends(get_branch_context),
    service: UnitService = Depends(get_unit_service),
) -> UnitOut:
    return await service.create_unit(branch_id=branch_ctx.branch_id, unit_in=unit_in)


@router.get(
    "/{unit_id}",
    response_model=UnitOut,
    status_code=status.HTTP_200_OK,
    summary="Get unit by id",
    description="Retrieve unit details by ID within the current branch.",
)
async def get_unit(
    unit_id: UUID,
    branch_ctx: BranchContext = Depends(get_branch_context),
    service: UnitService = Depends(get_unit_service),
) -> UnitOut:
    return await service.get_unit(branch_id=branch_ctx.branch_id, unit_id=unit_id)


@router.get(
    "",
    response_model=Page[UnitOut],
    status_code=status.HTTP_200_OK,
    summary="List units",
    description="List units in the current branch with filtering and pagination.",
)
async def list_units(
    type: Optional[UnitType] = Query(None, description="Filter by unit type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search name or code"),
    branch_id: Optional[UUID] = Query(None, description="Branch ID (must match current branch context)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Literal["name", "code", "created_at"] = Query("name", description="Sort field"),
    order: Literal["asc", "desc"] = Query("asc", description="Sort order"),
    branch_ctx: BranchContext = Depends(get_branch_context),
    service: UnitService = Depends(get_unit_service),
) -> Page[UnitOut]:
    effective_branch_id = branch_ctx.branch_id
    query = UnitListQuery(
        type=type,
        is_active=is_active,
        search=search,
        branch_id=branch_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )
    return await service.list_units(branch_id=effective_branch_id, query=query)


@router.patch(
    "/{unit_id}",
    response_model=UnitOut,
    status_code=status.HTTP_200_OK,
    summary="Update unit",
    description="Partially update a unit in the current branch.",
)
async def update_unit(
    unit_id: UUID,
    unit_in: UnitUpdate,
    branch_ctx: BranchContext = Depends(get_branch_context),
    service: UnitService = Depends(get_unit_service),
) -> UnitOut:
    return await service.update_unit(
        branch_id=branch_ctx.branch_id, unit_id=unit_id, unit_in=unit_in
    )


@router.delete(
    "/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete unit",
    description="Soft-delete a unit in the current branch.",
)
async def delete_unit(
    unit_id: UUID,
    branch_ctx: BranchContext = Depends(get_branch_context),
    service: UnitService = Depends(get_unit_service),
) -> None:
    await service.delete_unit(branch_id=branch_ctx.branch_id, unit_id=unit_id)

