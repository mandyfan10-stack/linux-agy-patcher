# Источники и атрибуция

Этот репозиторий не связан с Google. Antigravity CLI (`agy`) — продукт Google.

Код и подход собраны из открытых проектов и публичных DNS-сервисов. Ниже — что откуда взято.

## Стратегия обхода 400 «User location is not supported»

**[confeden/Antigravity](https://github.com/confeden/Antigravity)** (релизы вплоть до v2.10.0_3, 26 Aug 2026)

Репозиторий: https://github.com/confeden/Antigravity  
Релизы: https://github.com/confeden/Antigravity/releases

Оттуда:

- Ошибка 400 на `daily-cloudcode-pa.googleapis.com` зависит от **исходного IP**, а не от локального eligibility-экрана.
- `cloudcode-pa.googleapis.com` провайдеры перестали подменять; рабочий хост — `daily-cloudcode-pa.googleapis.com`.
- Переменная `CLOUD_CODE_URL` у CLI (`agy` читает её в `UpdateEndpointURL`).
- `HTTPS_PROXY` для Go language server: CONNECT, TLS **насквозь**, без своего сертификата.
- Переименование protobuf-поля `ineligible` → `inexigible` (та же длина).
- Детекция подмены DNS: ответ сравнивается с 8.8.8.8 / 1.1.1.1; `172.217.x` — настоящий Google, не прокси.
- Список провайдеров из `src/resolvers.rs`: xbox-dns.ru, comss.one, geohide.ru.
- v2.9.1_30–33: не закрывать простой туннель (пул Antigravity / «размышление» модели), карантин мёртвого края на 5 минут, не держать медленный маршрут после восстановления.
- v2.10.0_3: keepalive до 10 с простоя (иначе IDE крутит Authenticating), не доверять IP, который только принимает TCP и молчит, быстрый failover вместо 15 с.

Их «быстрый маршрут» (закрытый релей и ключ) **в этот репозиторий не входит** — в публичные исходники confeden его тоже не кладут.

## Байт-патч бинаря `agy` (x86-64)

**[AvenCores/open-antigravity-patcher](https://github.com/AvenCores/open-antigravity-patcher)** (GPL-3.0)

Репозиторий: https://github.com/AvenCores/open-antigravity-patcher  
Сигнатуры: `source/patcher/agy/patcher.py`, `source/patcher/manager/patcher.py`

Оттуда:

- Gate eligibility CLI: `cmp byte [rax+8], 0` → `test rax, rax; nop` (`48 85 c0 90`).
- Gate `hasValidAuth=true` у language_server: `80 78 08 00 74 ..` → `c6 40 08 01 90 90`.

Прямой предок сигнатур: [QNIX-Dev/eligibility-antigravity-patcher](https://github.com/QNIX-Dev/eligibility-antigravity-patcher) (MIT), как указано в README AvenCores.

## DNS / SNI-прокси, которые ещё подменяют CloudCode

Проверено с российского IPv4 (август 2026):

| Провайдер | DNS | `daily-cloudcode-pa.googleapis.com` |
|---|---|---|
| Google 8.8.8.8 | 8.8.8.8 | `172.217.x` — настоящий Google |
| [xbox-dns.ru](https://xbox-dns.ru/) | 111.88.96.50 / .51 | `172.217.x` — **больше не подменяет** (см. confeden v2.9.1.2) |
| [comss.one](https://comss.one/) | 83.220.169.155 и др. | `172.217.x` — не подменяет этот хост |
| [geohide.ru](https://dns.geohide.ru:8443/) | 45.155.204.190, 37.230.192.51 | прокси `45.155.204.190` / `37.230.192.51` (`95.182.120.241` с RU не отвечает) |

Этот патчер ходит на IP geohide CONNECT-прокси с SNI `daily-cloudcode-pa.googleapis.com`. TLS завершает Google, сертификат не подменяется.

## Что здесь своё

- Linux-обёртка `agy` + user systemd-сервис.
- Локальный CONNECT-прокси с липким IP и параллельным failover по двум IP geohide.
- Установщик, который патчит `~/.local/bin/agy` и не трогает системный DNS/`hosts`.
