import functools
import inspect
from uuid import UUID
from src.infrastructure.logger import app_logger

async def validate_home_membership(home_repository, user_id: UUID, home_id: UUID):
    """
    Core authorization logic. Verifies home existence and user membership.
    Returns the Home object if successful.
    """
    if not user_id or not home_id:
        app_logger.warning("Access check failed: Missing user_id or home_id")
        raise ValueError("User ID and Home ID are required")

    home = await home_repository.get_by_id(home_id)
    if not home:
        app_logger.warning(f"Access check failed: Home {home_id} does not exist")
        raise ValueError("Home retrieval failed")

    if not home.is_member(user_id):
        app_logger.warning(f"SECURITY WARNING: User {user_id} attempted unauthorized access to home {home_id}")
        raise ValueError("User is not a member of the home")
    
    return home

def require_house_access(func):
    """
    Decorator that enforces house access.
    
    Supports:
    - user_id + home_id (Direct)
    - user_id + list_id (Resolves home_id via shopping_repo)
    - DTOs containing these fields.
    
    Injection:
    - If the method has a 'home' parameter, the fetched Home object is injected.
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        
        user_id = bound_args.arguments.get('head_user_id') or \
                  bound_args.arguments.get('user_id') or \
                  bound_args.arguments.get('current_head_id')
        home_id = bound_args.arguments.get('home_id') or bound_args.arguments.get('target_home_id')
        list_id = bound_args.arguments.get('id') # ShoppingListService uses 'id' for list_id
        
        # 1. Extract from DTO if needed
        if not home_id or not user_id:
            for arg_value in bound_args.arguments.values():
                if hasattr(arg_value, 'home_id') and hasattr(arg_value, 'user_id'):
                    home_id = arg_value.home_id
                    user_id = arg_value.user_id
                    break

        # 2. Resolve home_id from list_id if home_id is missing (for ShoppingListService)
        if not home_id and list_id and hasattr(self, 'shopping_repo'):
            shopping_list = await self.shopping_repo.get_by_id(list_id)
            if not shopping_list:
                raise ValueError(f"Shopping list not found: {list_id}")
            home_id = shopping_list.home_id

        # 3. Perform the check
        home = await validate_home_membership(self._home_repository, user_id, home_id)

        # 4. Inject 'home' object if requested by the method signature
        if 'home' in bound_args.arguments:
            kwargs['home'] = home
        
        return await func(self, *args, **kwargs)
    
    return wrapper
