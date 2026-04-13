from fastapi import APIRouter, Depends
from api.routes.blog.generate import router as generate_router
from api.routes.blog.review import router as review_router
from api.routes.blog.status import router as status_router
from api.routes.blog.final_post import router as final_post_router
from api.routes.blog.user_posts import router as user_posts_router
from api.routes.blog.stream import router as stream_router
from backend.api.utils.auth import get_current_user


blog_router = APIRouter(prefix="/blog", tags=["Blog Generation"], dependencies=[Depends(get_current_user)])
blog_router.include_router(generate_router)
blog_router.include_router(review_router)
blog_router.include_router(status_router)
blog_router.include_router(final_post_router)
blog_router.include_router(user_posts_router)
blog_router.include_router(stream_router)
