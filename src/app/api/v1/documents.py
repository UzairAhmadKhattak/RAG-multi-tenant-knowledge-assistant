from fastapi import APIRouter,File,UploadFile,Form,status,Depends
from src.app.core.constants import (AccessLevel,
                                    UPLOADS_FOLDER,
                                    UPLOADS_PATH)
from src.app.utils.docs_helpers import save_file
from src.app.models import Document,User
from src.app.utils.query_helpers import get_or_create
from src.app.schemas.base import GeneralResponse
from src.app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.api.deps import get_current_user
from src.app.services.embed import embed_file
from fastapi import HTTPException

doc_router = APIRouter()

@doc_router.post("/upload",response_model=GeneralResponse)
async def upload_doc(file: UploadFile = File(...),
                     access_level:AccessLevel = Form(...),
                     title:str = Form(...),
                     db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)
    ):
    file_url = f"{UPLOADS_FOLDER}/{file.filename}"
    file_path = f"{UPLOADS_PATH}/{file.filename}"
    mime_type = await save_file(file_path=file_path,file=file)
    organization_id = user.organization_id
    user_id = user.id
    doc, created = await get_or_create(db, 
                                 Document, 
                                 title = title, 
                                 defaults={"file_path":file_url,
                                           "uploaded_by_id":user_id,
                                           "organization_id":organization_id
                                           }
                                )
    if created is False:
        raise HTTPException(
            status_code=400,
            detail='Document with this title already exists'
        )
    await embed_file(db,file_path,mime_type,organization_id,access_level,doc.id)
    await db.commit()
    await db.close()
    return {'detail':'Document successfully uploaded'}