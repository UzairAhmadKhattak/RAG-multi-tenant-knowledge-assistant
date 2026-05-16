
import magic
from fastapi import HTTPException, UploadFile
from src.app.core.constants import ALLOWED_MIME_TYPES
import aiofiles

def detect_type(header):
    """Detect the file type"""
    
    return magic.from_buffer(header, mime=True)

def is_safe_file(mime_type):
    """Check if the file is safe"""
    
    if mime_type not in ALLOWED_MIME_TYPES:
        return False
    return True

async def save_file(file_path: str,file: UploadFile):
    """Save the file if the file type is correct and safe"""
    
    header = await file.read(2048)
    file.file.seek(0)
    mime_type = detect_type(header)
    is_safe = is_safe_file(mime_type)

    if is_safe and mime_type.startswith('text'):
        try:
            async with aiofiles.open(file_path,'w') as f:
                while chunk := await file.read(1024*1024):
                    await f.write(chunk)
        except TypeError:
            file.file.seek(0)
            async with aiofiles.open(file_path,'wb') as f:
                while chunk := await file.read(1024*1024):
                    await f.write(chunk)    
    elif is_safe:
        async with aiofiles.open(file_path,'wb') as f:
            while chunk := await file.read(1024*1024):
                await f.write(chunk)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {mime_type}"
        )
    return mime_type