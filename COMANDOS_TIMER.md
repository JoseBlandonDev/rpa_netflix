# Comandos del timer

> **Este documento se reorganizó.** Su contenido está ahora repartido en la documentación por temas:
>
> | Buscabas | Ahora está en |
> |---|---|
> | Comandos del timer, arrancar/detener, ejecución manual | [Manual de operación](docs/OPERACION.md) |
> | `AUTO_DELETE_EMAILS`, `IMAP_TIMEOUT`, ventana de 5 minutos | [Configuración](docs/CONFIGURACION.md) |
> | Correos que no se eliminan, timeouts, informes que no llegan | [Solución de incidencias](docs/INCIDENCIAS.md) |
> | Por qué el sistema funciona por ciclos | [Arquitectura](docs/ARQUITECTURA.md) |
>
> Punto de entrada: [README](README.md).

## Chuleta

```bash
# Estado y próxima ejecución
systemctl status rpa_system.timer
systemctl list-timers rpa_system.timer

# Arrancar / detener / reiniciar
sudo systemctl start rpa_system.timer
sudo systemctl stop rpa_system.timer
sudo systemctl restart rpa_system.timer

# Un ciclo ahora mismo
sudo systemctl start rpa_system.service

# Logs
tail -f rpa_system.log
sudo journalctl -u rpa_system.service -n 50
```
