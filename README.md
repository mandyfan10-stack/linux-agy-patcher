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
4. Локальный CONNECT-прокси `127.0.0.1:18080`: только CloudCode → IP geohide, остальное напрямую.
5. user systemd-сервис `agy-cloudcode-proxy.service`.

Браузер, curl и прочие программы **не** получают системный прокси.

## Установка

Нужны: установленный `agy` (обычно `~/.local/bin/agy`), Python 3, systemd user-сессия.

```bash
git clone https://github.com/mandyfan10-stack/linux-agy-patcher.git
cd linux-agy-patcher
chmod +x install.sh uninstall.sh
./install.sh
```

Закройте текущий `agy` и запустите заново.

После `agy update`:

```bash
agy-repatch
```

Откат:

```bash
./uninstall.sh
```

## Ограничения

- Сигнатуры проверены на **agy 1.1.20 linux-amd64**. Другая версия: патчер откажется менять файл, если байты не найдены.
- geohide иногда меняет/глушит адреса — прокси перебирает три IP. Если все умрут, снова будет 400.
- «Быстрый релей» confeden сюда не входит (его нет в публичном git).
- ARM64-сигнатуры AvenCores в этот репозиторий не переносились.

## Лицензия

[GNU GPL v3](LICENSE) — как у [open-antigravity-patcher](https://github.com/AvenCores/open-antigravity-patcher), откуда взяты байт-сигнатуры.
