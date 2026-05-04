# Sistema de Login y Dashboard - Flask

Un sistema de autenticación completo con login, registro y dashboard funcional usando Flask, HTML, CSS y JavaScript.

## 📋 Características

✅ Login y Registro en la misma página
✅ Autenticación con sesiones seguras
✅ Base de datos SQLite integrada
✅ Dashboard con múltiples secciones
✅ Gestión de perfil de usuario
✅ Cambio de contraseña
✅ Diseño responsive y moderno
✅ Validaciones en frontend y backend

## 🚀 Instalación

### 1. Crear y activar entorno virtual

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: **http://localhost:5000**

## 📁 Estructura del proyecto

```
auth_system/
├── app.py                    # Backend Flask principal
├── requirements.txt          # Dependencias de Python
├── templates/
│   ├── index.html           # Página de login y registro
│   └── dashboard.html       # Dashboard principal
├── static/
│   ├── css/
│   │   ├── style.css        # Estilos de login
│   │   └── dashboard.css    # Estilos del dashboard
│   └── js/
│       ├── auth.js          # JavaScript de autenticación
│       └── dashboard.js     # JavaScript del dashboard
└── usuarios.db              # Base de datos SQLite (se crea automáticamente)
```

## 🔐 Credenciales de prueba

Puedes crear una cuenta directamente desde la pantalla de registro.

## 🛠️ Funcionalidades

### Login
- Acceso con email y contraseña
- Opción "Recordarme"
- Validaciones de campos

### Registro
- Crear nueva cuenta con:
  - Nombre completo
  - Email
  - Empresa (opcional)
  - Contraseña (mínimo 6 caracteres)
- Login automático después del registro

### Dashboard
- **Resumen**: Vista general de estado contable
- **Transacciones**: Gestión de movimientos
- **Reportes**: Generación de reportes
- **Cuentas**: Gestión de cuentas bancarias
- **Configuración**: 
  - Actualizar perfil
  - Cambiar contraseña

## 🔧 Configuración importante

En el archivo `app.py`, línea 14:

```python
app.config['SECRET_KEY'] = 'tu_clave_secreta_cambiar_en_produccion'
```

**IMPORTANTE**: Cambia esta clave en producción por una más segura.

## 📚 Endpoints API

### Autenticación
- `POST /api/login` - Iniciar sesión
- `POST /api/registro` - Registrarse
- `POST /api/logout` - Cerrar sesión

### Usuario
- `GET /api/usuario-info` - Obtener información del usuario
- `PUT /api/actualizar-perfil` - Actualizar perfil
- `POST /api/cambiar-contraseña` - Cambiar contraseña

## 🌐 Navegación

### Login
- Toggle entre login y registro
- Validación de campos
- Mensajes de error/éxito

### Dashboard
- Menú lateral con navegación
- Vista responsive
- Menú de usuario en la esquina superior derecha

## 📱 Responsive

El sistema es responsive y funciona en:
- 📱 Dispositivos móviles
- 💻 Tablets
- 🖥️ Escritorio

## 🎨 Personalización

### Cambiar colores
Edita las variables CSS en el inicio de los archivos CSS:

```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #1e40af;
    /* ... más colores */
}
```

### Agregar más secciones al dashboard
1. Agrega una nueva `<section>` en `dashboard.html`
2. Agrega un nuevo `<li>` en el menú
3. Añade el listener en `dashboard.js`

## 🐛 Solución de problemas

### Puerto 5000 en uso
```bash
python app.py --port 5001
```

### Base de datos corrupta
Elimina el archivo `usuarios.db` y vuelve a ejecutar la aplicación.

### Errores de módulos
```bash
pip install --upgrade -r requirements.txt
```

## 📝 Notas

- Las contraseñas se guardan encriptadas con Werkzeug
- Las sesiones expiran después de 7 días
- El timeout de sesión se resetea con actividad del usuario
- Todo el código está documentado y comentado

## 🤝 Próximas mejoras

Puedes agregar:
- Recuperación de contraseña por email
- Autenticación de dos factores (2FA)
- Integración con Google/GitHub OAuth
- Notificaciones por email
- Panel de administración
- Logs de actividad
- Exportación de reportes

## 📞 Soporte

Para más información sobre Flask: https://flask.palletsprojects.com/
Para más información sobre SQLAlchemy: https://www.sqlalchemy.org/

---

**Creado con ❤️ para tu software contable**
