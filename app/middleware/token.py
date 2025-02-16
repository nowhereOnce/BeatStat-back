from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.spotify import refresh_token

class RefreshTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Excluir los endpoints /login y /callback
        if request.url.path in ["/login", "/callback"]:
            return await call_next(request)

        try:
            # Pasar la solicitud al endpoint
            response = await call_next(request)

            # Si la respuesta es 401 (No autorizado), intentar refrescar el token
            if response.status_code == 401:
                refresh_token_value = request.cookies.get("refresh_token")
                if not refresh_token_value:
                    return RedirectResponse("/")

                # Refrescar el token
                new_access_token = refresh_token(refresh_token_value)

                # Crear una nueva respuesta y establecer la cookie
                response = Response()
                response.set_cookie(
                    key="access_token",
                    value=new_access_token,
                    max_age=3600,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                )

                # Actualizar el encabezado de autorización y volver a llamar al endpoint
                request.headers["Authorization"] = f"Bearer {new_access_token}"
                response = await call_next(request)

        except Exception as e:
            # Manejar errores inesperados
            response = Response(content=str(e), status_code=500)

        return response