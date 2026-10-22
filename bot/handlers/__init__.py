from bot.handlers.common import router as common_router
from bot.handlers.seller import router as seller_router
from bot.handlers.buyer import router as buyer_router

routers = [common_router, seller_router, buyer_router]
