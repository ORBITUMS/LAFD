HELP_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Помощь — Account Browser</title>
<style>
    * { box-sizing: border-box; }
    body {
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
        background: linear-gradient(135deg, #17171c 0%, #0e0e12 100%);
        color: #e4e4e8;
        max-width: 760px;
        margin: 0 auto;
        padding: 48px 28px 96px;
        line-height: 1.65;
        font-size: 15px;
    }
    h1 {
        font-size: 34px;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 4px;
        background: linear-gradient(135deg, #ffffff 0%, #9ba8b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    h2 {
        font-size: 19px;
        font-weight: 600;
        margin-top: 36px;
        color: #8ab4f8;
    }
    p { margin: 8px 0; }
    ul { padding-left: 22px; }
    li { margin: 6px 0; }
    kbd {
        display: inline-block;
        background: linear-gradient(180deg, #333338, #242428);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 5px;
        padding: 2px 7px;
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size: 12px;
        box-shadow: 0 1px 0 rgba(0,0,0,0.4);
    }
    code {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.06);
        padding: 2px 7px;
        border-radius: 5px;
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size: 13px;
        color: #c8d0da;
    }
    .muted { color: #808088; font-size: 14px; }
    .card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 18px 22px;
        margin: 16px 0;
    }
    .footer {
        margin-top: 64px;
        padding-top: 24px;
        border-top: 1px solid rgba(255,255,255,0.06);
    }
</style>
</head>
<body>

<h1>Account Browser</h1>
<p class="muted">Специализированный браузер-органайзер с изолированными, отдельными и защищёнными сессиями.</p>

<h2>Что такое сессия?</h2>
<p>Каждая сессия — это полностью изолированное хранилище куки, кэша и данных сайтов. Разные сессии не пересекаются: можно одновременно держать несколько Google-аккаунтов, разные профили на одном сайте и т.д. — без «выход/вход» и без режима инкогнито.</p>

<h2>Создание сессии</h2>
<ul>
    <li>Нажмите <kbd>+</kbd> слева на нижней панели.</li>
    <li>Введите имя сессии (например, «Рабочий Google») и нажмите <kbd>Enter</kbd>.</li>
</ul>

<h2>Управление сессиями</h2>
<ul>
    <li><b>Управление</b> — клик ПКМ по сессии.</li>
</ul>

<h2>От Разраба oWo </h2>
<ul>
    <li><b>Не работает дип сик?</b> — Перезагрузи страницу :)</li>
    <li><b>хочешь что-либо предложить добавить или нашёл баг?</b> — Пиши мне в тг @xd450</li>
</ul>


<h2>Где хранятся данные</h2>
<div class="card">
    <p>Список и настройки:</p>
    <p><code>~/.local/share/account-browser/profiles.json</code><br>
       <code>~/.local/share/account-browser/settings.json</code></p>
    <p>Данные каждой сессии:</p>
    <p><code>~/.local/share/account-browser/profiles/&lt;id&gt;/</code></p>
    <p class="muted">Чтобы перенести все сессии на другую машину — скопируйте весь каталог <code>account-browser/</code>.</p>
</div>

<div class="footer">
    <p class="muted">Версия 1.0b · Эта страница — временная документация, будет дополнена по мере развития приложения. XD</p>
</div>

</body>
</html>
"""