# План исправления разрешения и отображения

> Составлен: 2026-08-13  
> Статус: черновик, код пока не менялся

## Как сейчас устроено

```
game_config.json (width / height / fullscreen)
    ↓
_configure_panda3d()  →  win-size, fullscreen (PRC)
    ↓
ShowBase.__init__()
    ↓
_setup_window()  →  WindowProperties.requestProperties()
    ↓
_delayed_camera_setup (+0.1s)
    ↓
_update_camera_aspect_ratio()  →  OrthographicLens, view_width=70
```

| Слой | Где | Поведение при resize |
|------|-----|----------------------|
| `aspect2d` | HUD, меню, пауза, диалоги | Сохраняет пропорции (letterbox) |
| `render2d` | Фон главного меню | Растягивается на всё окно |
| `render` | Сцены, спрайты, игрок | Зависит от orthographic lens камеры |

**Настройки Resolution** (`main_menu.py`):

| Кнопка | Размер | Fullscreen |
|--------|--------|------------|
| 1280 x 720 (Windowed) | 1280×720 | false |
| 1600 x 900 (Windowed) | 1600×900 | false |
| 1920 x 1080 (Fullscreen) | 1920×1080 | true |

**Камера:** ширина frustum всегда 70 world units, высота = `70 / aspect`.  
**Сцены:** пещера/минигame ~70×36 (16:9), кухня 100×60 (больше камеры).

---

## Выявленные проблемы

### P0 — критично (ощущение «разрешение сломано»)

| # | Проблема | Файл | Симптom |
|---|----------|------|---------|
| 1 | Нет обработки resize окна | — (нет `window-event`) | В windowed при перетаскивании краёв камера не обновляется |
| 2 | Камера обновляется сразу после `requestProperties` | `game.py:224-228` | Lens может считаться по старому размеру окна |
| 3 | Resolution и fullscreen склеены в UI | `main_menu.py:481-483` | Нельзя 1920×1080 windowed |
| 4 | Нет индикации текущего пресета | `main_menu.py` | Непонятно, что активно |

### P1 — визуальные артефакты

| # | Проблема | Файл | Симптom |
|---|----------|------|---------|
| 5 | Фон меню на `render2d`, UI на `aspect2d` | `main_menu.py:44, 53` | На ultrawide / 4:3 фон тянется |
| 6 | Сцены под 16:9 | `cave.py:53` (70×36) | На 21:9 обрезается верх/низ |
| 7 | Кухня больше камеры, нет bounds | `kitchen.py:40` (100×60) | Часть комнаты за кадром |
| 8 | Один lens на все сцены | `game.py:336-371` | Нет учёта размера локации |

### P2 — качество кода

| # | Проблема | Файл |
|---|----------|------|
| 9 | Два способа сохранения config | `apply_resolution()` vs `_save_game_config()` |
| 10 | VSync только при `fps == 60` | `game.py:182` |
| 11 | Новый OrthographicLens на каждый update | `game.py:355-367` |
| 12 | Шрифты кириллицы в exe | `game.py:_setup_font()` (смежная UI-проблема) |

---

## План исправлений

### Этап 1 — стабильное окно и камера (1–2 дня)

**Цель:** смена разрешения и resize работают предсказуемо.

- [ ] Добавить `Game._on_window_event()` — подписка на `window-event`, debounce 1 кадр → `_update_camera_aspect_ratio()`
- [ ] Единый `_apply_display_settings(width, height, fullscreen)`:
  - `requestProperties`
  - `taskMgr.doMethodLater(0.1, _update_camera_aspect_ratio)` (как при старте)
- [ ] Надёжное чтение размера: `win.getXSize()/getYSize()`, fallback на config
- [ ] Расширенное логирование: config / фактический размер / aspect / frustum

**Критерий:** переключение пресетов + ручной resize в windowed не ломают пропорции мира.

---

### Этап 2 — настройки Resolution (0.5–1 день)

**Цель:** понятный UI.

- [ ] Разделить resolution и fullscreen (чекбокс Fullscreen отдельно)
- [ ] Подсветка активного пресета по `game_config["window"]`
- [ ] (Опционально) кнопка «System default» / detect native resolution

**Критерий:** любая комбинация width×height + fullscreen, виден текущий выбор.

---

### Этап 3 — мир и камера (2–3 дня)

**Цель:** все сцены одинаково на 16:9, 21:9, 4:3.

- [ ] Зафиксировать design target (16:9, view 70×39.4)
- [ ] Выбрать стратегию камеры:
  - **A. Fit height** — ultrawide: поля по бокам, без обрезки (рекомендуется)
  - **B. Fit width** — как сейчас, ultrawide режет верх/низ
  - **C. Cover + letterbox** — сложнее
- [ ] Унифицировать bounds сцен (cave / minigame / kitchen → ~70×36)
- [ ] `MOVEMENT_BOUNDS` для кухни
- [ ] Константы камеры в config: `"camera": { "view_width": 70, "design_aspect": 1.777 }`

**Критерий:** на 1920×1080, 2560×1080, 1280×720 видна вся локация без обрезки важного контента.

---

### Этап 4 — UI polish (1 день)

- [ ] Фон меню: `render2d` → `aspect2d`
- [ ] Settings panel на 720p windowed
- [ ] Один `_save_game_config()` для всех сохранений
- [ ] Пересборка exe после изменений

---

## Чеклист тестирования

| Сценарий | Ожидание |
|----------|----------|
| Старт 1920×1080 fullscreen | Меню + пещера без артефактов |
| 1280×720 windowed | UI читаем, мир по центру |
| Смена пресета из pause → Config | Камера совпадает с окном |
| Resize окна мышью | Камера обновляется за 1–2 кадра |
| Ultrawide 2560×1080 | Нет обрезки пола/потолка (после этапа 3) |
| Перезапуск | Сохранённое разрешение применяется |

---

## Рекомендуемый порядок

```
0. [СЕЙЧАС] Проверить game.log: window= vs config 1920×1080
1. Fullscreen → native resolution монитора + lens по фактическому размеру
2. window-event + отложенный lens update
3. UI: fullscreen отдельно + подсветка пресета
4. меню render2d → aspect2d
5. камера fit-height + унификация сцен
```

---

## Открытые вопросы

1. **Главный симптom (ответ пользователя, 2026-08-13):**
   - **Растянуто** — картинка не сохраняет пропорции
   - **Не то разрешение на мониторе** — вероятно да (игра не попадает в native resolution)

2. **Fullscreen:** native монитора или фиксированные 1920×1080? → **уточнить** (сейчас в config жёстко 1920×1080 + fullscreen)
3. **Ultrawide:** поддерживаем или достаточно 16:9? → **уточнить**

---

## Диагноз под текущие симптомы

**Config сейчас:** `1920×1080`, `fullscreen: true` (`config/game_config.json`).

### Почему «растянуто»

| Источник | Механизм |
|----------|----------|
| **Fullscreen + фиксированный win-size** | Panda3D/Windows может вывести fullscreen в **native** разрешении монитора (2560×1440, 1366×768 и т.д.), а камера/config считают 1920×1080 → aspect не совпадает → мир и UI ведут себя по-разному |
| **Фон меню на `render2d`** | Растягивается на весь framebuffer без letterbox; кнопки на `aspect2d` — нет → визуально «всё криво» особенно в меню |
| **Lens по config fallback** | Если `getXSize()/getYSize()` возвращает 0 при старте, lens берёт 1920×1080 из config, а окно уже другое (`game.py:346-349`) |

### Почему «не то разрешение на мониторе»

- В fullscreen **нет запроса native resolution** — только `win-size 1920 1080` в PRC.
- На мониторе ≠ 1920×1080 ОС часто **масштабирует** или **растягивает** буфер.
- Нет логики «узнать размер экрана → применить его в fullscreen».

### Что делать в первую очередь (минимальный fix)

```
Приоритет A (1 PR, ~2–4 ч):
1. При fullscreen — получить native resolution (WindowProperties.getDisplaySize() / win.getProperties())
2. Применять именно его в requestProperties, писать в config
3. window-event → _update_camera_aspect_ratio() при любом изменении размера
4. Отложенный lens update и при apply_resolution (как при старте)

Приоритет B (следом):
5. Фон меню: render2d → aspect2d
6. UI Resolution: fullscreen отдельно от width×height + показ текущего режима в логе/HUD
```

### Как проверить гипотезу

После запуска посмотреть `game.log`:

```
Window properties set: 1920x1080, fullscreen=True
Camera lens updated: aspect=..., window=????x????
```

Если `window=` **не** 1920×1080 — это и есть причина растяжения; fix из приоритета A.

---

## Ключевые файлы

| Файл | Роль |
|------|------|
| `config/game_config.json` | width, height, fullscreen |
| `src/core/game.py` | PRC, window, camera lens |
| `src/scenes/main_menu.py` | Resolution tab |
| `src/scenes/cave.py` | Background 70×36 |
| `src/scenes/kitchen.py` | Background 100×60 |
| `src/scenes/minigame.py` | MOVEMENT_BOUNDS |
| `src/entities/player.py` | Collision bounds |
| `src/ui/hud.py` | aspect2d HUD |
