# Manual de operación

Todo lo que se hace en el día a día. Los comandos asumen conexión SSH al servidor:

```bash
cd /root/automatizacion
```

---

## Índice

- [Ver si está funcionando](#ver-si-está-funcionando)
- [Ver qué ha procesado](#ver-qué-ha-procesado)
- [Detener el sistema](#detener-el-sistema)
- [Volver a arrancarlo](#volver-a-arrancarlo)
- [Ejecutar un ciclo ahora mismo](#ejecutar-un-ciclo-ahora-mismo)
- [Pedir un informe en Excel](#pedir-un-informe-en-excel)
- [El menú interactivo](#el-menú-interactivo)
- [Consultar la base de datos](#consultar-la-base-de-datos)
- [Espacio en disco](#espacio-en-disco)

---

## Ver si está funcionando

```bash
systemctl status rpa_system.timer
```

Debe decir `active (waiting)`: el timer está vivo, esperando el próximo disparo.

**Cuándo fue y cuándo será la próxima ejecución:**

```bash
systemctl list-timers rpa_system.timer
```

```
NEXT                        LEFT  LAST                        PASSED  UNIT
Fri 2026-07-31 21:22:30 UTC 5s    Fri 2026-07-31 21:22:00 UTC 24s ago rpa_system.timer
```

**Cómo terminó la última ejecución:**

```bash
systemctl status rpa_system.service
```

Busca `Result=success`. Como el servicio es de tipo `oneshot`, es **normal y correcto** que aparezca como `inactive (dead)`: se ejecuta y termina. No significa que esté apagado.

**La prueba definitiva** — que el log siga creciendo:

```bash
tail -5 rpa_system.log
```

La última línea debe tener menos de un minuto de antigüedad.

---

## Ver qué ha procesado

```bash
# Actividad reciente
tail -30 rpa_system.log

# En tiempo real
tail -f rpa_system.log

# Solo errores
grep "ERROR" rpa_system.log | tail -20

# Solo lo relevante (ignorando el ruido de "no hay correos")
grep -vE "No hay correos|Encontrados 0|Tablas de base" rpa_system.log | tail -30
```

Ese último comando es el más útil: en un sistema que se ejecuta 2880 veces al día, la mayoría de las líneas dicen "no había nada que hacer".

**Buscar qué pasó con un correo concreto:**

```bash
grep -i "asunto o remitente" rpa_system.log
```

**Ver los días anteriores** (el log rota cada noche):

```bash
ls -lt rpa_system.log*
grep "ERROR" rpa_system.log.2026-07-30
```

---

## Detener el sistema

```bash
sudo systemctl stop rpa_system.timer
```

Eso detiene los disparos futuros. Si hay un ciclo ejecutándose en ese instante, lo termina normalmente (dura un par de segundos).

**Para que siga detenido después de reiniciar el servidor:**

```bash
sudo systemctl disable rpa_system.timer
```

Comprobar que quedó detenido:

```bash
systemctl is-active rpa_system.timer    # debe decir: inactive
```

> Mientras está detenido, los correos de Netflix **siguen llegando pero no se procesan**. Al reactivarlo solo se recuperarán los de los últimos 5 minutos: el resto quedará sin procesar, no en cola.

---

## Volver a arrancarlo

```bash
sudo systemctl start rpa_system.timer
sudo systemctl enable rpa_system.timer   # que arranque solo al reiniciar el servidor
```

Verificar:

```bash
systemctl list-timers rpa_system.timer
```

---

## Ejecutar un ciclo ahora mismo

Sin esperar al timer:

```bash
sudo systemctl start rpa_system.service
```

Ver el resultado:

```bash
tail -20 rpa_system.log
```

**Para pruebas, ejecutándolo directamente y viendo la salida en pantalla:**

```bash
cd /root/automatizacion
python3 rpa/main.py
```

Esto hace exactamente lo mismo que el timer y escribe en el mismo log, con la ventaja de que ves la salida en vivo.

---

## Pedir un informe en Excel

Sin entrar al servidor: **envía un correo con la palabra `REPORTE`** (en el asunto o en el cuerpo) a la cuenta configurada. En menos de un minuto recibirás la respuesta con el Excel del historial adjunto.

Funciona desde cualquier remitente, y el informe se envía a quien lo pidió.

**Generar el Excel a mano en el servidor:**

```bash
cd /root/automatizacion
python3 -c "from rpa.database import Database; print(Database().export_to_excel())"
```

Queda en `reporte_rpa.xlsx`.

---

## El menú interactivo

Para quien prefiera no memorizar comandos:

```bash
cd /root/automatizacion
./gestionar_rpa_timer.sh
```

Ofrece: estado del timer y del servicio, ver logs (archivo y `journalctl`), iniciar/detener/reiniciar, ejecución manual y próximas ejecuciones programadas.

---

## Consultar la base de datos

Todo lo procesado queda en SQLite. Consultas útiles:

```bash
cd /root/automatizacion

# Últimos 10 procesados con éxito
sqlite3 rpa_database.db "SELECT timestamp, sender, status FROM rpa_success ORDER BY id DESC LIMIT 10;"

# Últimos 10 fallidos, con el motivo
sqlite3 rpa_database.db "SELECT timestamp, sender, status, observations FROM rpa_failed ORDER BY id DESC LIMIT 10;"

# Cuántos de cada tipo hay
sqlite3 rpa_database.db "SELECT status, COUNT(*) FROM rpa_success GROUP BY status;"
sqlite3 rpa_database.db "SELECT status, COUNT(*) FROM rpa_failed GROUP BY status;"

# Actividad de hoy
sqlite3 rpa_database.db "SELECT COUNT(*) FROM rpa_success WHERE date(timestamp) = date('now');"
```

Si `sqlite3` no está instalado: `apt install sqlite3`.

> Los registros de más de 30 días se borran solos, una vez al día.

---

## Espacio en disco

```bash
df -h /
du -sh /root/automatizacion/*  | sort -h | tail -5
du -sh ~/.cache/selenium/
```

El sistema se mantiene solo:

| Qué | Cómo se limpia |
|---|---|
| `rpa_system.log` | Rota cada noche; conserva 30 días |
| Registros de la base de datos | Se borran los de más de 30 días, a diario |
| Caché de Selenium | Se limpia cada 7 días |

Limpieza manual de la caché de Selenium, si hiciera falta:

```bash
rm -rf ~/.cache/selenium/chrome/linux64/*
rm -rf ~/.cache/selenium/chromedriver/linux64/*
```

Se vuelve a descargar sola en la siguiente ejecución.
