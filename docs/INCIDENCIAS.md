# Solución de incidencias

Organizado por síntoma.

---

## Triaje rápido

| Lo que ves | Ve a |
|---|---|
| El log no crece / no se procesa nada | [El sistema no se está ejecutando](#el-sistema-no-se-está-ejecutando) |
| Todos los correos salen como `NO_URL` | [No encuentra el enlace](#no-encuentra-el-enlace) |
| Todos los correos salen como `FAILED` | [Encuentra el enlace pero no pulsa el botón](#encuentra-el-enlace-pero-no-pulsa-el-botón) |
| `Error obteniendo correos` en el log | [Fallo de conexión con el correo](#fallo-de-conexión-con-el-correo) |
| `Timeout` en el log | [Timeouts de IMAP](#timeouts-de-imap) |
| No llega el Excel al pedir `REPORTE` | [Los informes no llegan](#los-informes-no-llegan) |
| Llegan correos pero no se procesan | [Llegan correos y no pasa nada](#llegan-correos-y-no-pasa-nada) |
| Disco lleno | [Espacio en disco](#espacio-en-disco) |

---

## El sistema no se está ejecutando

**Síntoma:** `tail -5 rpa_system.log` muestra líneas de hace mucho rato.

Diagnóstico en orden:

```bash
# 1. ¿El timer está activo?
systemctl is-active rpa_system.timer

# 2. ¿Cuándo debería dispararse?
systemctl list-timers rpa_system.timer

# 3. ¿Cómo terminó la última ejecución?
systemctl status rpa_system.service

# 4. ¿Qué dice el journal?
sudo journalctl -u rpa_system.service -n 50 --no-pager
```

| Hallazgo | Causa | Solución |
|---|---|---|
| El timer está `inactive` | Se detuvo, o no está habilitado tras reiniciar | `sudo systemctl enable --now rpa_system.timer` |
| El timer está activo pero el servicio falla | El script revienta al arrancar | Mirar el `journalctl` del paso 4 |
| `status=1/FAILURE` repetido | Error de Python (dependencia, `.env` mal) | Ejecutar a mano: `python3 rpa/main.py` |
| Todo parece bien | Puede que **sí** esté funcionando | Ver la nota de abajo |

> **Cuidado con un falso positivo:** `systemctl status rpa_system.service` muestra `inactive (dead)` **incluso cuando todo va bien**. El servicio es de tipo `oneshot`: se ejecuta y termina. Lo que hay que mirar es `Result=success` y que el log crezca.

**La comprobación que no engaña:**

```bash
date; tail -2 rpa_system.log
```

Si la última línea del log tiene menos de un minuto, el sistema funciona.

---

## No encuentra el enlace

**Síntoma:** en el log, repetidamente:

```
WARNING - No se encontró URL que coincida con el patrón configurado
```

y en la base de datos se acumulan registros `NO_URL`.

**Causa más probable: Netflix cambió la URL de confirmación.** El sistema busca enlaces que empiecen por `LINK_PATTERN`; si Netflix cambia esa dirección, ninguno coincide.

**Cómo confirmarlo:** abre uno de esos correos en tu bandeja, copia la dirección real del botón de confirmación y compárala con la configurada:

```bash
grep LINK_PATTERN /root/automatizacion/.env
```

**Solución:** actualiza `LINK_PATTERN` en el `.env` con el nuevo patrón. Usa la parte estable de la URL, sin los identificadores que cambian en cada correo.

**Otras causas posibles:**

- Están llegando correos de Netflix que sencillamente no son de confirmación de ubicación (promociones, facturas). Es normal que esos den `NO_URL`.
- El correo llegó solo en texto plano y el enlace venía cortado en varias líneas.

---

## Encuentra el enlace pero no pulsa el botón

**Síntoma:** en el log aparece `URL encontrada` pero después un error de Selenium, y se acumulan registros `FAILED`.

**Causa más probable: Netflix rediseñó la página** y el selector del botón ya no vale.

```bash
grep BUTTON_SELECTOR /root/automatizacion/.env
```

**Solución:** abrir el enlace en un navegador de escritorio, inspeccionar el botón de confirmación y actualizar `BUTTON_SELECTOR` con un selector CSS que lo identifique.

**Otras causas:**

| Causa | Cómo se reconoce | Solución |
|---|---|---|
| El enlace ya caducó | Falla siempre, incluso a mano | Ninguna: hay que reaccionar más rápido |
| Chrome/Chromium no está instalado o se actualizó | `Error inicializando Chrome driver` | Limpiar la caché de Selenium (abajo) |
| La página tarda más que `TIMEOUT_SECONDS` | Falla de forma intermitente | Subir `TIMEOUT_SECONDS` en el `.env` |

**Limpiar la caché de Selenium** (soluciona la mayoría de los problemas de driver):

```bash
rm -rf ~/.cache/selenium/chrome/linux64/*
rm -rf ~/.cache/selenium/chromedriver/linux64/*
```

Se vuelve a descargar sola en la siguiente ejecución.

---

## Fallo de conexión con el correo

**Síntoma:** `ERROR - Error obteniendo correos no leídos: ...` en el log.

```bash
grep "Error obteniendo correos" /root/automatizacion/rpa_system.log | tail -5
```

| Mensaje | Causa | Solución |
|---|---|---|
| `AUTHENTICATIONFAILED` | Contraseña incorrecta o caducada | Generar una nueva contraseña de aplicación |
| `Name or service not known` | Sin DNS o sin red | Revisar la conectividad del servidor |
| `Connection refused` | Puerto o servidor mal configurados | Revisar `IMAP_SERVER` e `IMAP_PORT` |

El caso más habitual con diferencia es que **la contraseña de aplicación fue revocada**: pasa si se cambia la contraseña de la cuenta de Google o se revisan los accesos. Hay que generar otra y actualizar `EMAIL_PASSWORD` (y `EMAIL_PASS` si es la misma cuenta).

---

## Timeouts de IMAP

**Síntoma:**

```bash
grep "Timeout" /root/automatizacion/rpa_system.log | tail -10
```

```
ERROR - Timeout obteniendo correos (más de 30 segundos)
ERROR - Timeout marcando como leído (más de 30 segundos)
ERROR - Timeout eliminando correo (más de 30 segundos)
```

**Esto no es un fallo grave.** Es la protección funcionando: en lugar de quedarse colgado, el sistema abandona la operación, la registra y termina el ciclo. El siguiente arranca 30 segundos después.

**Cuándo preocuparse:** si aparecen constantemente. Entonces el servidor de correo o la red están lentos:

```env
IMAP_TIMEOUT=60
```

Si un timeout ocurre justo al marcar un correo como leído, ese correo se reprocesará en el ciclo siguiente. Por eso existe la ventana de 5 minutos: limita cuántas veces puede repetirse.

---

## Los informes no llegan

**Síntoma:** envías un correo con `REPORTE` y no recibes nada.

Comprobaciones en orden:

```bash
cd /root/automatizacion

# 1. ¿Vio la solicitud?
grep -i "reporte" rpa_system.log | tail -10

# 2. ¿Está configurado el SMTP?
grep -E "^EMAIL_(HOST|PORT|USER)" .env

# 3. ¿Se generó el Excel?
ls -l reporte_rpa.xlsx
```

| Hallazgo | Causa | Solución |
|---|---|---|
| No aparece nada de "reporte" en el log | El correo no se leyó | Debe estar **no leído** y haber llegado en los últimos 5 minutos |
| `Error generando reporte Excel` | Fallo al exportar la base de datos | Probar a mano (ver abajo) |
| No hay variables `EMAIL_HOST`/`EMAIL_USER` | Falta la configuración SMTP | Añadirlas al `.env` |
| Todo correcto pero no llega | Filtro de spam | Revisar la carpeta de spam del remitente |

**Probar la generación del Excel a mano:**

```bash
cd /root/automatizacion
python3 -c "from rpa.database import Database; print(Database().export_to_excel())"
```

> Recuerda: la solicitud tiene que llegar **en los últimos 5 minutos** y estar **sin leer**. Un correo antiguo no dispara nada.

---

## Llegan correos y no pasa nada

**Síntoma:** ves correos de Netflix en la bandeja pero el sistema no los toca.

| Comprobación | Comando / Acción |
|---|---|
| ¿Están **sin leer**? | Solo procesa no leídos. Uno abierto por un humano se ignora |
| ¿Llegaron hace menos de 5 minutos? | La ventana es corta a propósito |
| ¿El remitente coincide? | `grep SENDER_FILTER .env` — debe corresponderse con el remitente real |
| ¿Lee la bandeja correcta? | `grep EMAIL_ADDRESS .env` |
| ¿El sistema está corriendo? | [Arriba](#el-sistema-no-se-está-ejecutando) |

La causa más común: **alguien abrió el correo antes que el bot**. Al quedar marcado como leído, deja de ser candidato. Para reprocesarlo, márcalo como no leído desde el cliente de correo (y hazlo dentro de la ventana de 5 minutos... o mejor, reenvíatelo).

---

## Espacio en disco

```bash
df -h /
du -sh /root/automatizacion/* | sort -h | tail -5
du -sh ~/.cache/selenium/
```

El sistema se mantiene solo: el log rota cada noche conservando 30 días, los registros de más de 30 días se borran a diario y la caché de Selenium se limpia cada 7 días.

Si aun así necesitas espacio:

```bash
# Borrar los logs rotados más viejos
ls -t /root/automatizacion/rpa_system.log.* | tail -n +8 | xargs rm -f

# Vaciar la caché de Selenium
rm -rf ~/.cache/selenium/chrome/linux64/*
rm -rf ~/.cache/selenium/chromedriver/linux64/*
```

> **Nunca borres `rpa_database.db`**: es el historial completo de todo lo procesado y la fuente de los informes en Excel. Si necesitas reducirlo, la limpieza automática ya se ocupa de los registros antiguos.

---

## Cuándo llamar al desarrollador

- `LINK_PATTERN` y `BUTTON_SELECTOR` actualizados y aun así falla todo.
- Errores de Python en `journalctl` que no se resuelven reinstalando dependencias.
- La base de datos está corrupta o hay que cambiar su estructura.
- Hay que modificar la lógica: otra ventana de tiempo, otro proveedor de correo, otro flujo.

Información útil para el diagnóstico:

```bash
cd /root/automatizacion
{
  systemctl status rpa_system.timer --no-pager
  systemctl status rpa_system.service --no-pager
  tail -100 rpa_system.log
} > /tmp/diagnostico_rpa.txt
```
