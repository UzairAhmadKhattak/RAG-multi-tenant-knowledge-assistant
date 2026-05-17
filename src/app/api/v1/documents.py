from fastapi import APIRouter,File,UploadFile,Form,status,Depends
from src.app.core.constants import (UPLOADS_FOLDER,
                                    UPLOADS_PATH)
from src.app.utils.docs_helpers import save_file
from src.app.models import Document,User,UserRole
from src.app.utils.query_helpers import update_or_create
from src.app.schemas.base import GeneralResponse
from src.app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.api.deps import get_current_user
from src.app.services.embed import embed_file
from src.app.services.summarizer import summaries_document

doc_router = APIRouter()

@doc_router.post("/upload",response_model=GeneralResponse)
async def upload_doc(file: UploadFile = File(...),
                     role:UserRole = Form(...),
                     title:str = Form(...),
                     db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)
    ):
    file_url = f"{UPLOADS_FOLDER}/{file.filename}"
    file_path = f"{UPLOADS_PATH}/{file.filename}"
    mime_type = await save_file(file_path=file_path,file=file)
    document_summary = await summaries_document(file)
    organization_id = user.organization_id
    user_id = user.id
    doc, created = await update_or_create(db, 
                                 Document, 
                                 title = title, 
                                 defaults={"file_path":file_url,
                                           "uploaded_by_id":user_id,
                                           "organization_id":organization_id,
                                           'summary':document_summary
                                           }
                                )
    await embed_file(db,file_path,mime_type,organization_id,role,doc.id,True)
    await db.commit()
    await db.close()
    if created:
        return {'detail':'Document successfully uploaded'}
    return {'detail':'Document successfully updated'}