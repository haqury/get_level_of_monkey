# 📋 Главное меню - Руководство

## 🎮 **Что добавлено:**

### **1. Главное меню** ✅
- ✅ Красивый title screen
- ✅ Кнопка "Играть"
- ✅ Кнопка "Выход"
- ✅ Статус BrainLink в реальном времени
- ✅ Информация об управлении

### **2. Система запуска BrainLink** ✅
- ✅ **Автоматический поиск** BrainLinkClient
- ✅ **Автозапуск** если найден
- ✅ **Проверка подключения** к Shared Memory
- ✅ **Сохранение пути** для быстрого запуска
- ✅ **Fallback** на клавиатуру если BrainLink недоступен

---

## 🚀 **Как это работает:**

### **При запуске игры:**

```
1. Игра запускается
   ↓
2. Показывается главное меню
   ↓
3. Автоматическая проверка BrainLink:
   
   a) Проверяет: Запущен ли BrainLinkClient?
      └─> Да: ✅ "Connected" → можно играть
      └─> Нет: переход к б)
   
   b) Проверяет: Знаем путь к BrainLinkClient?
      └─> Да: используем сохраненный путь
      └─> Нет: ищем в стандартных местах:
          - $BRAINLINK_CLIENT_DIR$
          - ~/PycharmProjects/BrainLinkClient
          - ~/Projects/BrainLinkClient
          - ../BrainLinkClient (относительно игры)
   
   c) Найден?
      └─> Да: Запускаем BrainLinkClient
          └─> Ждем подключения (10 сек)
              └─> Подключился: ✅ "Connected"
              └─> Timeout: ⚠️ "Timeout" (можно играть без BrainLink)
      └─> Нет: ❌ "Not Found" (можно играть без BrainLink)
   
4. Кнопка "Играть" активируется
   ↓
5. Игрок нажимает "Играть"
   ↓
6. Начинается игра!
```

---

## 📊 **Статусы BrainLink в меню:**

| Статус | Значок | Описание | Можно играть? |
|--------|--------|----------|---------------|
| **Checking...** | ⏳ | Проверка при запуске | ❌ Подожди |
| **Searching...** | ⏳ | Поиск BrainLinkClient | ❌ Подожди |
| **Launching...** | 🚀 | Запуск BrainLinkClient | ❌ Подожди |
| **Connecting...** | ⏳ | Ожидание Shared Memory | ❌ Подожди |
| **✅ Connected** | ✅ | Всё готово! | ✅ ДА |
| **❌ Not Found** | ❌ | BrainLink не найден | ✅ ДА (клавиатура) |
| **⚠️ Timeout** | ⚠️ | Запустился, но не подключился | ✅ ДА (клавиатура) |
| **❌ Launch Failed** | ❌ | Ошибка запуска | ✅ ДА (клавиатура) |

---

## 🎮 **Пользовательский опыт:**

### **Сценарий 1: BrainLink установлен и работает**
```
1. Запускаешь игру
2. Меню показывает: "✅ Connected"
3. Нажимаешь "Играть"
4. Играешь с BrainLink! 🧠
```

### **Сценарий 2: BrainLink установлен, но не запущен**
```
1. Запускаешь игру
2. Меню показывает: "⏳ Searching..." → "🚀 Launching..." → "⏳ Connecting..."
3. Через 2-3 секунды: "✅ Connected"
4. Нажимаешь "Играть"
5. Играешь с BrainLink! 🧠
```

### **Сценарий 3: BrainLink не установлен**
```
1. Запускаешь игру
2. Меню показывает: "⏳ Searching..." → "❌ Not Found"
3. Инфо: "Playing without BrainLink"
4. Нажимаешь "Играть"
5. Играешь с клавиатурой ⌨️
```

### **Сценарий 4: BrainLink в нестандартном месте**
```
1. Запускаешь игру
2. Меню показывает: "❌ Not Found"
3. Вручную запускаешь BrainLink из своей папки
4. В меню статус меняется на: "✅ Connected" (игра обнаруживает Shared Memory)
5. Нажимаешь "Играть"
6. Играешь с BrainLink! 🧠
```

---

## 💾 **Сохранение пути:**

При первом обнаружении BrainLinkClient, путь сохраняется в:
```
config/brainlink_path.json
```

**Пример:**
```json
{
  "brainlink_path": "$BRAINLINK_CLIENT_DIR$"
}
```

При следующем запуске игра сразу использует этот путь!

---

## 🔧 **Технические детали:**

### **BrainLinkLauncher класс:**

```python
# Поиск BrainLink
path = launcher.find_brainlink_client()

# Проверка запущен ли
is_running = launcher.is_running()  # Проверяет Shared Memory

# Запуск
success = launcher.launch(path)

# Ожидание подключения
connected = launcher.wait_for_connection(timeout=10.0)
```

### **Места поиска:**
1. `$BRAINLINK_CLIENT_DIR$`
2. `~/PycharmProjects/BrainLinkClient`
3. `~/Projects/BrainLinkClient`
4. `../BrainLinkClient` (относительно игры)

### **Запуск:**
```bash
# Windows
pythonw main.py  # Без консольного окна

# Linux/Mac
python3 main.py
```

---

## 🎨 **UI Элементы:**

```
┌─────────────────────────────────────┐
│                                     │
│      Fucking Pickup                 │  <- Title (желтый)
│   2D Action with BrainLink          │  <- Subtitle (серый)
│                                     │
│  ┌───────────────────────────────┐  │
│  │ 🧠 BrainLink Status:          │  │
│  │                               │  │
│  │ ✅ Connected                  │  │ <- Status (цветной)
│  │ BrainLink is ready!           │  │ <- Info
│  └───────────────────────────────┘  │
│                                     │
│         ┌─────────┐                 │
│         │ Играть  │  <- Enabled     │ <- Play button (зеленая)
│         └─────────┘                 │
│                                     │
│         ┌─────────┐                 │
│         │ Выход   │                 │ <- Quit button (красная)
│         └─────────┘                 │
│                                     │
│  Controls: Arrow Keys or BrainLink  │  <- Info (серый)
│                                     │
└─────────────────────────────────────┘
```

---

## 🐛 **Troubleshooting:**

### **Проблема: "❌ Not Found"**
**Решение:**
1. Проверь что BrainLinkClient установлен
2. Убедись что `main.py` находится в корне BrainLinkClient
3. Попробуй запустить BrainLink вручную
4. Или переместите BrainLinkClient в стандартное место

### **Проблема: "⚠️ Timeout"**
**Решение:**
1. BrainLinkClient запустился, но не создал Shared Memory
2. Проверь в BrainLink: включен ли "Enable Shared Memory"
3. Подключено ли устройство / запущен ли Simulator
4. Можешь играть с клавиатурой

### **Проблема: "❌ Launch Failed"**
**Решение:**
1. Проверь права доступа к папке BrainLinkClient
2. Проверь что Python установлен
3. Попробуй запустить BrainLink вручную

---

## 📝 **Лог файлы:**

Все действия логируются в `game.log`:

```
INFO - BrainLinkLauncher initialized
INFO - ✅ Found BrainLinkClient at: C:\...\BrainLinkClient
INFO - ✅ BrainLinkClient launched (PID: 12345)
INFO - Waiting for BrainLink connection (timeout: 10.0s)...
INFO - ✅ Connected to BrainLink!
INFO - 🎮 Starting game!
```

---

## 🎯 **Итог:**

✅ **Полностью автоматическая система!**
- Находит BrainLink
- Запускает если нужно
- Проверяет подключение
- Дает играть в любом случае

**Игрок просто запускает игру и играет!** 🎮🧠

---

**Дата:** 2026-01-20  
**Версия:** v0.3.0
