# Оффлайн без аккаунта в Horizon-лаунчере

Разбор того, почему `horizon-launcher play` отказывает без аккаунта и как играть
полностью оффлайн. Выяснено на лаунчере nightly (2026-10-29); исходники —
`launcher/src` в репозитории Horizon.

## Суть

Лаунчер Horizon не запускает игру без учётной записи, владеющей Minecraft:
Java Edition. Оффлайн-имя (singleplayer, LAN, offline-mode серверы) по умолчанию
можно завести только «рядом» с такой учёткой. Полностью без аккаунта разрешает
скрытая опция разработчика.

## Ключевые места в коде

### `account.rs`

- `OFFLINE_NEEDS_OWNER` — сообщение
  *«Offline names need a Microsoft account that owns Minecraft: Java Edition
  in the launcher»*; возвращается, когда оффлайн-имя заводят без владельца.
- `Accounts::play_as_with(store, who, offline_without_owner)` — флаг
  `offline_without_owner`, который разрешает оффлайн-имя без владельца.
- `launch_for_game(..., offline_without_owner)` — гейт перед запуском: при
  `NoOwner` и включённом флаге игра стартует оффлайн (`Launch::default()`).
- `session_for_game(game_home, offline_without_owner)` — обёртка над
  `launch_for_game`.

### `backend.rs`

- `client()` (её вызывает CLI-`play`) вызывает `session_for_game(..., false)` —
  **`false` захардкожен**. Поэтому `horizon-launcher play` никогда не запускает
  оффлайн без владельца, даже если `dev_offline` включён.
- `download_for_owner()` — скачивание версии из Mojang **только для владельца**
  (опция разработчика игру не скачивает; файлы должны быть в локальной папке).

### `main.rs` (окно)

- `let offline_without_owner = self.settings.dev_offline;` — окно **уважает**
  настройку и передаёт её в `session_for_game`.

### `dev_options.rs`

- Секция «Developer options» скрыта; раскрывается после **7 кликов** по версии
  лаунчера в сайдбаре (или видна, если `dev_offline` уже включён).

### `backend.rs` (`Settings`)

- `dev_offline: bool` — хранится в `settings.json` под ключом `"dev_offline"`,
  по умолчанию `false`, в файле отсутствует, пока выключен.

## Как включить

1. **GUI**: 7 кликов по версии в сайдбаре → Настройки → Developer options →
   «Offline names without an account».
2. **Файл**: добавить `"dev_offline": true` в
   `$env:APPDATA\horizon-launcher\settings.json` (в `cmd.exe` —
   `%APPDATA%\horizon-launcher\settings.json`).

После этого запускать игру **из окна**, не через `horizon-launcher play`.

## Вывод

Оффлайн-README от slycat555 писался под лаунчер `v0.2.32`, где гейт был мягче.
На свежих nightly для полного оффлайна нужны два условия: `dev_offline = true`
и запуск из GUI-окна.
