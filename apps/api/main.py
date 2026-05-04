from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import os

app = FastAPI(
    title="Nexopus Finance Ops — API",
    description="Motor contábil com IA para DRE, Balanço e relatórios financeiros.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Valida JWT Bearer token. Substituir pela lógica real de JWT."""
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    # TODO: decodificar e validar JWT (ex.: python-jose)
    return {"token": token}


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "ledger-ai-api"}


@app.post("/documents/upload", tags=["documents"])
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Recebe um arquivo (PDF/Excel/SPED), persiste no storage e enfileira parsing."""
    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/plain"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Tipo de arquivo não suportado")

    doc_id = str(uuid.uuid4())
    # TODO: salvar arquivo no S3/MinIO e registrar no DB
    # TODO: enfileirar tasks.process_document.delay(doc_id)
    return {"status": "processing", "doc_id": doc_id, "filename": file.filename}


@app.get("/reports/dre/{company_id}/{year}", tags=["reports"])
def get_dre(
    company_id: str,
    year: int,
    current_user: dict = Depends(get_current_user),
):
    """Gera DRE (Demonstrativo de Resultado do Exercício) para a empresa e ano."""
    # TODO: from services.accounting_core.engine import AccountingEngine
    # engine = AccountingEngine(db_session)
    # return engine.generate_dre(company_id, year)
    return {"company_id": company_id, "year": year, "type": "DRE", "data": {}}


@app.get("/reports/balance/{company_id}/{year}", tags=["reports"])
def get_balance_sheet(
    company_id: str,
    year: int,
    current_user: dict = Depends(get_current_user),
):
    """Gera Balanço Patrimonial para a empresa e ano."""
    # TODO: from services.accounting_core.engine import AccountingEngine
    # engine = AccountingEngine(db_session)
    # return engine.generate_balance_sheet(company_id, year)
    return {"company_id": company_id, "year": year, "type": "balanco", "data": {}}
