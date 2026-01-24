# 🎮 get_level_of_monkey

2D Action игра с видом сверху на движке **Panda3D** с интеграцией **BrainLink** через Shared Memory!

## 🎯 Особенности

- 🧠 **Управление мыслями** через BrainLink
- ⚡ Система энергии и HP
- 🎭 RPG элементы: диалоги, прокачка
- 🐵 Мини-игра "Обезьянья атака"
- 🎨 Pixel-art графика
- 📊 Интеграция с BrainLink Client через Shared Memory

## 🚀 Установка

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

## 🎮 Запуск

```bash
python main.py
```

## 🕹️ Управление

### Клавиатура:
- **Стрелки**: Движение (вверх, вниз, влево, вправо)
- **Space**: Взаимодействие/Диалог

### BrainLink (Shared Memory):
- **ml** (Move Left): Влево
- **mr** (Move Right): Вправо
- **mu** (Move Up): Вверх
- **md** (Move Down): Вниз
- **stop**: Остановка

## 📁 Структура проекта

```
get_level_of_monkey/
├── main.py                 # Точка входа
├── config/                 # Конфигурация
│   ├── game_config.json    # Параметры игры
│   └── balance.json        # Баланс
├── src/
│   ├── core/               # Ядро игры
│   │   ├── game.py         # Главный класс игры
│   │   ├── scene_manager.py # Менеджер сцен
│   │   └── input_manager.py # Управление вводом
│   ├── systems/            # Игровые системы
│   │   ├── energy_system.py # Энергия
│   │   ├── health_system.py # Здоровье
│   │   ├── dialog_system.py # Диалоги
│   │   └── progression_system.py # Прокачка
│   ├── entities/           # Игровые объекты
│   │   ├── player.py       # Игрок
│   │   ├── npc.py          # NPC
│   │   └── monkey.py       # Обезьяны
│   ├── scenes/             # Сцены/Локации
│   │   ├── cave.py         # Пещера
│   │   ├── kitchen.py      # Кухня
│   │   └── minigame.py     # Мини-игра
│   ├── ui/                 # Интерфейс
│   │   ├── hud.py          # HUD
│   │   └── dialog_box.py   # Диалоговые окна
│   └── integration/        # Интеграция
│       └── brainlink.py    # Shared Memory с BrainLink
├── assets/                 # Ресурсы
│   ├── sprites/            # Спрайты
│   ├── sounds/             # Звуки
│   └── music/              # Музыка
└── requirements.txt
```

## 🔗 Интеграция с BrainLink

1. Запустите **BrainLink Client** (из директории `$BRAINLINK_CLIENT_DIR$`)
2. Подключите устройство или запустите Simulator
3. Включите **☑ Enable Shared Memory** в UI
4. Запустите игру: `python main.py`
5. Игра автоматически подключится к BrainLink!
6. **Управляйте мыслями!** 🧠

**Проверка подключения:**
```
✅ Connected to BrainLink: 'brainlink_data'  # В логах
❌ BrainLink not found                        # Если не подключен
```

## 📊 Технологии

- **Panda3D 1.10.13+** - игровой движок
- **Python 3.8+** - язык программирования
- **Shared Memory** - интеграция с BrainLink (~0.01ms латентность!)
- **JSON** - конфигурация и баланс
- **DirectGUI** - UI система Panda3D

## 📦 Версия

**Текущая: v0.2.0** - Полная игра! 🎉

См. [CHANGELOG.md](CHANGELOG.md) для деталей.

## 🎯 Игровой процесс

### Локации:
1. **Пещера** - стартовая локация (отец, выход в кухню)
2. **Кухня** - локация с мамой
3. **Мини-игра** - "Обезьянья атака"

### Системы:
- ⚡ **Энергия** - расходуется при движении
- ❤️ **Здоровье** - уменьшается от урона
- 📈 **Прокачка** - опыт и улучшения
- 💬 **Диалоги** - общение с NPC

## 🐵 Мини-игра "Обезьянья атака"

- Уклоняйся от летящих какашек!
- 4 типа обезьян (разная скорость/точность)
- 8-12 обезьян на поле
- Цель: выжить как можно дольше!

## 👤 Автор

Разработано с 🧠 BrainLink интеграцией!
