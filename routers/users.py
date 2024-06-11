from fastapi import APIRouter, Request, Form
from starlette.responses import HTMLResponse

from sqlalchemy.orm import Session
from fastapi import Depends

import models
from database import engine, SessionLocal

from starlette.responses import RedirectResponse
from starlette import status

from routers.auth import get_current_user, get_password_hash, verify_password

from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory='templates')


@router.get('/edit', response_class=HTMLResponse)
async def change_password(request: Request):
    print('進入 edit')
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse('change-password.html', {'request': request, 'user': user})


@router.post('/edit', response_class=HTMLResponse)
async def change_password_commit(request: Request, db: Session = Depends(get_db),
                                 password: str = Form(...),
                                 new_password: str = Form(...),
                                 new_password2: str = Form(...)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)

    if new_password != new_password2:
        msg = 'confirmed password not validate'
        return templates.TemplateResponse('change-password.html', {'request': request, 'msg': msg})

    user_model = db.query(models.Users).filter(models.Users.username == user.get('username')).first()

    if not verify_password(password, user_model.hashed_password):
        msg = 'wrong old password'
        return templates.TemplateResponse('change-password.html', {'request': request, 'msg': msg})

    hashed_new_password = get_password_hash(new_password)
    user_model.hashed_password = hashed_new_password

    db.add(user_model)
    db.commit()
    msg = 'Password updated'
    request.session["msg"] = msg
    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)
