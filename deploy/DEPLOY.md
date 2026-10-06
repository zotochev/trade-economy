# Деплой на VPS (systemd + nginx)

Схема такая же, как у trade-news. Streamlit слушает только `127.0.0.1:10010`. Наружу его отдаёт
nginx на `https://kainode.duckdns.org/economy/`, с тем же сертификатом и тем же паролем, что у
админки trade-news. Данные обновляет отдельный таймер дважды в день.

| Файл | Что делает |
|---|---|
| `economy-model.service` | сам дашборд (`streamlit run app.py`) |
| `economy-model-update.service` | разовое обновление кэша (`update_data.py --force`) |
| `economy-model-update.timer` | запускает обновление в 13:00 и 22:30 UTC |
| `economy-model.nginx.conf` | `location /economy/` для существующего server-блока trade-news |

## 1. Код и окружение

```bash
sudo mkdir -p /opt/economy-model-lab && sudo chown crip: /opt/economy-model-lab
git clone git@github.com:zotochev/trade-economy.git /opt/economy-model-lab     # под пользователем crip
cd /opt/economy-model-lab
uv sync --no-dev            # uv сам скачает Python 3.13, если его нет
.venv/bin/python update_data.py   # первая загрузка всех рядов, ~1 мин
```

Если сервис будет работать не под `crip` или код лежит не в `/opt/economy-model-lab`,
поправьте `User=`, `WorkingDirectory=` и `ExecStart=` во всех трёх юнитах.
Пользователю нужно право на запись в `data_cache/`.

## 2. Юниты

```bash
sudo cp deploy/economy-model.service deploy/economy-model-update.service deploy/economy-model-update.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now economy-model economy-model-update.timer
```

Проверка: `curl http://127.0.0.1:10010/economy/_stcore/health` должен вернуть `ok`.

## 3. nginx

```bash
sudo cp deploy/economy-model.nginx.conf /etc/nginx/snippets/economy-model.conf
sudo nano /etc/nginx/sites-available/trade-news-admin
```

Внутри блока `server { listen 443 ... }`, **перед** `location /`, добавьте строку:

```nginx
    include /etc/nginx/snippets/economy-model.conf;
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Откройте https://kainode.duckdns.org/economy/. Браузер спросит пароль от админки trade-news.

Отдельный пароль для дашборда: создайте файл
`sudo htpasswd -c /etc/nginx/economy-model.htpasswd логин` и добавьте в `location /economy/`
строки `auth_basic "economy-model";` и `auth_basic_user_file /etc/nginx/economy-model.htpasswd;`.

## Обновление кода

```bash
cd /opt/economy-model-lab && git pull && uv sync --no-dev && sudo systemctl restart economy-model
```

## Логи и проверка

```bash
journalctl -u economy-model -f                 # дашборд
journalctl -u economy-model-update -n 100      # последнее обновление данных (OK/ERR по каждому ряду)
systemctl list-timers | grep economy-model     # когда следующее обновление
sudo systemctl start economy-model-update      # обновить данные прямо сейчас
```

Дашборд перечитывает кэш не реже раза в час, поэтому после обновления новые данные
появятся в течение часа. Сразу — кнопкой на странице «Данные».

## Если что-то не так

| Симптом | Что проверить |
|---|---|
| `502 Bad Gateway` | `systemctl status economy-model`; порт в юните и в `proxy_pass` один и тот же (10010) |
| Страница белая или крутится бесконечно | не проходит websocket: в `location` должны быть `Upgrade`/`Connection` и `proxy_http_version 1.1` |
| `404` на `/economy/` | `--server.baseUrlPath economy` в юните не совпадает с путём в nginx |
| `economy-model-update` в `failed` | `journalctl -u economy-model-update` — строки `ERR`. Чаще всего Yahoo временно отказывает облачным IP; FRED и Шиллер от этого не зависят, при следующем запуске обычно проходит |
