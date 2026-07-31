# Instalación en un servidor nuevo

Solo hace falta para migrar de servidor o levantar un entorno desde cero. El servidor actual ya está configurado.

---

## Requisitos

- Linux con `systemd`
- Python 3.7 o superior
- Google Chrome o Chromium (para Selenium)
- Una cuenta de correo con IMAP habilitado (y SMTP si se quieren los informes)
- Acceso root (el servicio corre como root)

---

## Pasos

### 1. Clonar el proyecto

```bash
cd /root
git clone https://github.com/JoseBlandonDev/rpa_netflix.git automatizacion
cd automatizacion
```

> La carpeta **debe llamarse `automatizacion`**: las unidades de `systemd` tienen esa ruta escrita (`WorkingDirectory`, `ExecStart`, `ReadWritePaths`). Si usas otro nombre, hay que editar `rpa_system.service`.

### 2. Instalar dependencias

```bash
pip3 install -r requirements.txt
```

Si prefieres aislarlo en un entorno virtual, recuerda que `rpa_system.service` invoca `/usr/bin/python3` directamente: tendrás que apuntar `ExecStart` al Python del entorno.

### 3. Configurar las credenciales

```bash
cp config/env.example .env
nano .env
```

Como mínimo hay que completar `EMAIL_ADDRESS` y `EMAIL_PASSWORD`. Detalle de cada variable: [Configuración](CONFIGURACION.md).

```bash
chmod 600 .env    # que solo root pueda leerlo
```

### 4. Instalar el servicio y el timer

```bash
sudo cp rpa_system.service /etc/systemd/system/
sudo cp rpa_system.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rpa_system.timer
```

`rpa_system.service` es de tipo `oneshot`: **no se habilita ni se arranca por separado**, lo dispara el timer.

### 5. Verificar

```bash
# El timer está vivo y con próxima ejecución programada
systemctl list-timers rpa_system.timer

# Un ciclo manual, viendo la salida
python3 rpa/main.py

# El log crece
tail -5 rpa_system.log
```

Una ejecución correcta con la bandeja vacía se ve así:

```
INFO - Iniciando sistema RPA en modo ciclo único...
INFO - Tablas de base de datos creadas/verificadas exitosamente
INFO - Leyendo correos de Netflix...
INFO - Encontrados 0 correos no leídos de los últimos 5 minutos
INFO - No hay correos de Netflix para procesar
```

### 6. Prueba de extremo a extremo

Envía a la cuenta configurada un correo con la palabra **`REPORTE`** en el asunto. En menos de un minuto deberías recibir la respuesta con el Excel adjunto. Eso confirma de una vez la lectura IMAP, la base de datos y el envío SMTP.

---

## Migrar desde un servidor existente

Además del código, hay que llevarse dos cosas que **no están en git**:

```bash
# Desde el servidor viejo
scp .env root@<servidor-nuevo>:/root/automatizacion/.env
scp rpa_database.db root@<servidor-nuevo>:/root/automatizacion/rpa_database.db
```

| Archivo | Por qué |
|---|---|
| `.env` | Credenciales y configuración |
| `rpa_database.db` | Todo el historial de correos procesados |

Los archivos de marca (`db_cleanup.flag`, `selenium_cleanup.flag`) no hace falta copiarlos: se regeneran solos.

**Acuérdate de detener el timer en el servidor viejo** antes de arrancar el nuevo, o ambos leerán la misma bandeja y competirán por los mismos correos:

```bash
# En el servidor viejo
sudo systemctl disable --now rpa_system.timer
```

---

## Actualizar el código

```bash
cd /root/automatizacion
sudo systemctl stop rpa_system.timer

cp rpa_database.db rpa_database.db.backup
git pull

# Solo si cambiaron las unidades de systemd
sudo cp rpa_system.service rpa_system.timer /etc/systemd/system/
sudo systemctl daemon-reload

sudo systemctl start rpa_system.timer
```

Verifica después con `tail -5 rpa_system.log` que los ciclos vuelven a registrarse.
