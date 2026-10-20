"""AI usage: how many tokens this staff member and their organization have used, and what's left."""

from fastapi import APIRouter, Depends

import allowances
import ledger
from deps import StaffCtx, current_staff

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("")
def usage(ctx: StaffCtx = Depends(current_staff)):
    """Everyone sees their own and their organization's totals; the admin also sees each colleague's."""
    return {**ledger.org_report(ctx.db, ctx.org.id, ctx.user.id, include_people=ctx.user.role == "admin"),
            "allowances": allowances.summary(ctx.org)}
