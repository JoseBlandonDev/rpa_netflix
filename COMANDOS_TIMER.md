# 🚀 Comandos Rápidos - Sistema RPA con Timer

## ⚡ Comandos Esenciales (Copia y pega)

### ✅ Verificar estado del timer
```bash
sudo systemctl status rpa_system.timer
```

### ✅ Verificar estado del servicio
```bash
sudo systemctl status rpa_system.service
```

### ⏹️ Detener el timer
```bash
sudo systemctl stop rpa_system.timer
```

### ▶️ Iniciar el timer
```bash
sudo systemctl start rpa_system.timer
```

### 🔄 Reiniciar el timer
```bash
sudo systemctl restart rpa_system.timer
```

### 🚀 Ejecutar manualmente
```bash
sudo systemctl start rpa_system.service
```

### 📊 Ver próximas ejecuciones
```bash
sudo systemctl list-timers rpa_system.timer
```

### 📋 Ver logs recientes
```bash
sudo journalctl -u rpa_system.service -n 20
```

### 🔍 Ver logs en tiempo real
```bash
sudo journalctl -u rpa_system.service -f
```

---

## 🎮 Gestor Interactivo

Para usar el gestor con menú:
```bash
./gestionar_rpa_timer.sh
```

---

## 🆘 Emergencias

### Detener todo inmediatamente
```bash
sudo systemctl stop rpa_system.timer
sudo systemctl stop rpa_system.service
```

### Reiniciar completamente
```bash
sudo systemctl restart rpa_system.timer
sudo systemctl status rpa_system.timer
```

---

## 📈 Información del Sistema

### Ver archivo de log
```bash
tail -20 rpa_system.log
```

### Ver base de datos
```bash
ls -la rpa_database.db
```

### Ver logs de hoy
```bash
sudo journalctl -u rpa_system.service --since today
```

---

## ⏰ Configuración del Timer

El sistema está configurado para ejecutarse:
- **Cada minuto** en punto (00 segundos)
- **En modo background** sin necesidad de terminal
- **Automáticamente** al reiniciar el servidor

### Verificar configuración del timer
```bash
sudo systemctl show rpa_system.timer
```

---

## 💡 Tips

- **El timer se ejecuta cada minuto** automáticamente
- **No necesitas terminal** - funciona en background
- **Se reinicia automáticamente** si el servidor se apaga
- **Los logs se guardan automáticamente**
- **Puedes ejecutar manualmente** cuando quieras

---

**🎯 ¡El sistema RPA ahora se ejecuta cada minuto en modo background!** 