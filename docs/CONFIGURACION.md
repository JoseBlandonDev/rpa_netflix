# Configuración

Todo se configura en un único archivo: **`.env`**, en la raíz del proyecto.

```bash
cd /root/automatizacion
nano .env
```

> **Los cambios se aplican solos.** Cada ejecución arranca un proceso nuevo que vuelve a leer el `.env` desde cero, así que lo que edites entra en vigor en el ciclo siguiente (como máximo, 30 segundos después). **No hace falta reiniciar ningún servicio.**

> ⚠️ El `.env` contiene contraseñas y no se sube a git. La plantilla completa está en `config/env.example`.

---

## Variables

### Lectura de correo (IMAP)

| Variable | Qué hace | Por defecto |
|---|---|---|
| `IMAP_SERVER` | Servidor de entrada | `imap.gmail.com` |
| `IMAP_PORT` | Puerto IMAP | `993` |
| `IMAP_TIMEOUT` | Segundos antes de abandonar una operación IMAP | `30` |
| `EMAIL_ADDRESS` | Cuenta que se lee | *(requerido)* |
| `EMAIL_PASSWORD` | Contraseña **de aplicación** de esa cuenta | *(requerido)* |

`IMAP_TIMEOUT` es la protección contra cuelgues: si el servidor de correo no responde, la operación se abandona, se registra el error y el ciclo termina. Sin esto, un proceso podría quedarse colgado indefinidamente. Súbelo si la red del servidor es lenta.

### Qué correos procesar

| Variable | Qué hace | Por defecto |
|---|---|---|
| `SENDER_FILTER` | Remitente cuyos correos se procesan | `netflix.com` |
| `LINK_PATTERN` | Fragmento de URL que identifica el enlace a pulsar | `https://www.netflix.com/account/update-primary-location` |

`LINK_PATTERN` es el filtro que decide qué enlace del correo es el bueno. Un correo de Netflix trae muchos enlaces (ayuda, cancelar suscripción, política de privacidad); solo se abre el que empieza por este patrón.

> Si Netflix cambia la URL de confirmación, **esta es la variable que hay que actualizar**. El síntoma será que todos los correos empiezan a registrarse como `NO_URL`.

### Automatización del navegador

| Variable | Qué hace | Por defecto |
|---|---|---|
| `BUTTON_SELECTOR` | Selector CSS del botón que hay que pulsar | `button[type="submit"]` |
| `TIMEOUT_SECONDS` | Espera máxima de carga de página y de aparición del botón | `10` |

> Si Netflix rediseña la página de confirmación, hay que actualizar `BUTTON_SELECTOR`. El síntoma será que todo se registra como `FAILED`: el enlace se encuentra y se abre, pero el botón no.

### Base de datos

| Variable | Qué hace | Por defecto |
|---|---|---|
| `DB_PATH` | Ruta del archivo SQLite | `rpa_database.db` |

### Eliminación automática de correos

```env
AUTO_DELETE_EMAILS=true
```

Valores que **activan**: `true`, `1`, `yes`, `on`
Valores que **desactivan**: `false`, `0`, `no`, `off`, o no definir la variable

Comportamiento según el desenlace del correo:

| Desenlace | Se registra como | ¿Se elimina el correo? |
|---|---|---|
| Clic correcto | `SUCCESS` | Sí |
| Clic fallido | `FAILED` | **No** — se conserva para poder revisarlo |
| Sin URL válida | `NO_URL` | Sí |
| Excepción durante el proceso | `ERROR` | Sí |
| Solicitud de informe atendida | *(no aplica)* | Sí |

Dos matices importantes:

- **Los registros de la base de datos se conservan siempre**, se elimine o no el correo. El historial nunca se pierde.
- **Los correos eliminados no se recuperan.** Si necesitas auditar manualmente la bandeja, pon `AUTO_DELETE_EMAILS=false`; los correos quedarán marcados como leídos pero seguirán ahí.

### Envío de informes (SMTP)

Necesario para la función de `REPORTE`:

| Variable | Qué hace | Por defecto |
|---|---|---|
| `EMAIL_HOST` | Servidor de salida | `smtp.gmail.com` |
| `EMAIL_PORT` | Puerto SMTP | `587` |
| `EMAIL_USER` | Cuenta remitente del informe | *(requerido)* |
| `EMAIL_PASS` | Contraseña de aplicación | *(requerido)* |

---

## Lo que no es configurable

Dos valores están fijos en el código, a propósito:

| Qué | Valor | Dónde |
|---|---|---|
| **Ventana de correos** | Últimos 5 minutos | `rpa/email_reader.py`, `get_unread_emails()` |
| **Frecuencia de ejecución** | Cada 30 segundos | `rpa_system.timer`, `OnCalendar=*:*:00/30` |

Para cambiar la frecuencia hay que editar el timer y recargar `systemd`:

```bash
sudo nano /etc/systemd/system/rpa_system.timer   # editar OnCalendar
sudo systemctl daemon-reload
sudo systemctl restart rpa_system.timer
```

> Las dos van juntas: si espacias las ejecuciones más de 5 minutos, empezarás a perder correos, porque la ventana de lectura dejará huecos sin cubrir.

---

## Configurar el correo con Gmail

1. Activa la verificación en dos pasos de la cuenta.
2. Genera una **contraseña de aplicación** (16 caracteres).
3. Úsala en `EMAIL_PASSWORD` y `EMAIL_PASS`.

La contraseña normal de la cuenta **no funciona**: Google la rechaza para IMAP y SMTP.

---

## Comprobar un cambio

Después de editar el `.env`:

```bash
cd /root/automatizacion

# Ejecutar un ciclo y ver la salida en directo
python3 rpa/main.py

# O esperar 30 segundos y mirar el log
tail -20 rpa_system.log
```

Si algo falla, restaura tu respaldo (`cp .env.backup .env`); el ciclo siguiente ya usará el archivo restaurado.
