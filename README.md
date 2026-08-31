# linux-agy-patcher

Патчер [Antigravity CLI](https://antigravity.google/docs/cli/install/) (`agy`) для Linux: снимает локальный eligibility-гейт и проводит CloudCode через DNS-подмену **без системного VPN**.

Не связан с Google. Работает только с уже установленным `agy`.

## Зачем это

С российского IP Gemini в `agy` падает так:

```
Agent execution terminated due to error.
FAILED_PRECONDITION (code 400): User location is not supported for the API use.
```

Логин и список моделей при этом проходят. 400 отвечает `daily-cloudcode-pa.googleapis.com` по **исходящему IP**.

Бинарный патч сам по себе 400 не лечит. Нужен маршрут, на котором этот хост резолвится не в `172.217.x` Google, а в SNI-прокси.

Подробные ссылки на исходники: [NOTICE.md](NOTICE.md).

## Что ставится

1. Байт-патч `agy` (eligibility + `hasValidAuth` + protobuf `ineligible` → `inexigible`).
2. Оригинал сохраняется как `~/.local/bin/agy.agybak`, рабочий ELF — `~/.local/bin/agy.real`.
3. `~/.local/bin/agy` становится обёрткой: `HTTPS_PROXY` + `CLOUD_CODE_URL`.
4. Локальный CONNECT-прокси `127.0.0.1:18080`: гонка DNS (dns-ai DoT / geohide / xbox-dns / comss против 8.8.8.8), только **подмена**, плюс TLS+SNI probe; иначе напрямую. Живой IP липкий, коннект — кто ответил первым. Простой туннель не режется (как confeden v2.9.1_30), мёртвый край — карантин 5 мин. Системный DNS не меняется.
5. user systemd: `agy-cloudcode-proxy.service`, `agy-watchdog.path` (`PathModified` на `agy`/`agy.real`) и `agy-watchdog.timer` (раз в 5 минут).
6. Обёртка перехватывает `agy update`: запускает настоящий апдейт, затем `agy-repatch` — даже если апдейтер затёр сам скрипт (процесс bash уже в памяти). Шаблон обёртки лежит отдельно (`agy-wrapper.tmpl`), апдейтер его не трогает.

Браузер, curl и прочие программы **не** получают системный прокси.

```bash
agy-patcher status   # обёртка, патч, прокси, watchdog
agy-patcher probe    # CONNECT + loadCodeAssist, ловит 400 location
agy-repatch          # вручную после апдейта
```

## Установка

Нужны: установленный `agy` (обычно `~/.local/bin/agy`), Python 3, systemd user-сессия.

```bash
git clone https://github.com/mandyfan10-stack/linux-agy-patcher.git
cd linux-agy-patcher
chmod +x install.sh uninstall.sh
./install.sh
```

Закройте текущий `agy` и запустите заново.

После `agy update` обёртка сама вызывает `agy-repatch`. Если апдейт обошёл обёртку (`agy.real update`, in-place truncate), сработают `PathModified` или таймер. Вручную:

```bash
agy-repatch
```

Откат:

```bash
./uninstall.sh
```

## Ограничения

- Сигнатуры проверены на **agy 1.1.20 linux-amd64**. Другая версия: обёртка всё равно восстановится, байт-патч пропустит неизвестные сигнатуры.
- geohide иногда меняет/глушит адреса — прокси держит липкий живой IP и параллельно пробует `45.155.204.190` / `37.230.192.51`. Если все умрут, снова будет 400.
- [dns-ai.ru](https://dns-ai.ru/) спрашивается только по DoT (`dns.dns-ai.ru:853`). Их UDP/53 закрыт, а с RU его ещё и перехватывают. Узел в NL (`186.246.45.126`) в FALLBACK не кладётся, пока не отвечает HTTP: иначе happy-eyeballs берёт молчащий TCP.
- «Быстрый релей» confeden сюда не входит (его нет в публичном git).
- ARM64-сигнатуры AvenCores в этот репозиторий не переносились.

## Лицензия

[GNU GPL v3](LICENSE) — как у [open-antigravity-patcher](https://github.com/AvenCores/open-antigravity-patcher), откуда взяты байт-сигнатуры.
