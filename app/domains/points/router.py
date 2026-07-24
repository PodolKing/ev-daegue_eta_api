from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/points", tags=["points"])


@router.get("/balance")
def balance():
    # TODO: point_wallets balance — week 2
    raise HTTPException(status_code=501, detail="points /balance not implemented")


@router.post("/charge-test")
def charge_test():
    # TODO: A안 테스트 충전 (dev only) — week 3
    raise HTTPException(status_code=501, detail="points /charge-test not implemented")


@router.get("/ledger")
def ledger():
    raise HTTPException(status_code=501, detail="points /ledger not implemented")
