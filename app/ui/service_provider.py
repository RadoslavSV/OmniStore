from app.services.store_app_service import StoreAppService

# One shared instance for the whole UI
store_app_service = StoreAppService.create_default()
