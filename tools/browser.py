import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

_browser = None
_page = None
_playwright = None

async def _ensure_browser():
    """Ленивая инициализация браузера с антидетект настройками."""
    global _browser, _page, _playwright
    if _browser is None:
        _playwright = await async_playwright().start()
        
        # Запускаем браузер с настройками для обхода детекции
        _browser = await _playwright.chromium.launch(
            headless=False,  # Используем видимый браузер (можно переключить на True если нужно)
            args=[
                '--disable-blink-features=AutomationControlled',  # Отключаем флаг автоматизации
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Создаем контекст с дополнительными настройками
        context = await _browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ru-RU',
            timezone_id='Europe/Moscow',
            permissions=['geolocation']
        )
        
        _page = await context.new_page()
        
        # Скрываем признаки автоматизации
        await _page.add_init_script("""
            // Переопределяем webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Добавляем chrome объект
            window.chrome = {
                runtime: {}
            };
            
            // Переопределяем permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Добавляем плагины
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Добавляем языки
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ru-RU', 'ru', 'en-US', 'en']
            });
        """)
    
    return _page

async def browser_navigate(url: str) -> Dict[str, Any]:
    """Открывает URL в браузере."""
    page = await _ensure_browser()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Небольшая задержка для имитации человеческого поведения
        await asyncio.sleep(1)
        
        title = await page.title()
        return {
            "success": True,
            "url": page.url,
            "title": title,
            "content_length": len(await page.content())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def browser_click(selector: str) -> Dict[str, Any]:
    """Кликает по элементу."""
    page = await _ensure_browser()
    try:
        await page.click(selector, timeout=10000)
        await asyncio.sleep(0.5)  # Имитация человеческого поведения
        return {"success": True, "selector": selector}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def browser_type(selector: str, text: str) -> Dict[str, Any]:
    """Вводит текст в поле."""
    page = await _ensure_browser()
    try:
        await page.fill(selector, text)
        await asyncio.sleep(0.3)  # Имитация человеческого поведения
        return {"success": True, "selector": selector, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def browser_get_text(selector: str = "body") -> Dict[str, Any]:
    """Получает текст элемента."""
    page = await _ensure_browser()
    try:
        text = await page.inner_text(selector)
        return {"success": True, "text": text[:5000]}  # Лимит для контекста
    except Exception as e:
        return {"success": False, "error": str(e)}

async def browser_screenshot(path: str = "screenshot.png") -> Dict[str, Any]:
    """Делает скриншот."""
    page = await _ensure_browser()
    try:
        await page.screenshot(path=path, full_page=True)
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def browser_search_google(query: str) -> Dict[str, Any]:
    """
    Выполняет поиск в Google и возвращает результаты.
    Использует антидетект меры для обхода блокировок.
    """
    page = await _ensure_browser()
    try:
        # Переходим на Google
        await page.goto("https://www.google.com", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)
        
        # Ищем поле поиска и вводим запрос
        search_input = await page.query_selector('textarea[name="q"], input[name="q"]')
        if search_input:
            await search_input.type(query, delay=100)  # Имитация печати человека
            await asyncio.sleep(0.5)
            await search_input.press("Enter")
            
            # Ждем загрузки результатов
            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(3)  # Увеличена задержка для полной загрузки
            
            # Извлекаем результаты поиска с множественными селекторами
            results = []
            
            # Пробуем разные селекторы для результатов поиска
            selectors_to_try = [
                'div.g',  # Классический селектор
                'div[data-sokoban-container]',  # Альтернативный
                'div.Gx5Zad',  # Новый формат
                'div[jscontroller][lang]',  # Еще один вариант
            ]
            
            search_results = []
            for selector in selectors_to_try:
                search_results = await page.query_selector_all(selector)
                if search_results:
                    break
            
            # Если не нашли результаты стандартными селекторами, пробуем найти все ссылки
            if not search_results:
                # Ищем все элементы с h3 (заголовки результатов)
                h3_elements = await page.query_selector_all('h3')
                for h3 in h3_elements:
                    try:
                        # Получаем родительский элемент с ссылкой
                        parent = await h3.evaluate_handle('el => el.closest("a") || el.parentElement.closest("a")')
                        if parent:
                            search_results.append(await h3.evaluate_handle('el => el.closest("div")'))
                    except:
                        continue
            
            # Обрабатываем найденные результаты
            for result in search_results[:10]:  # Берем первые 10 результатов
                try:
                    # Пробуем разные способы извлечения заголовка
                    title = ""
                    title_elem = await result.query_selector('h3')
                    if title_elem:
                        title = await title_elem.inner_text()
                    
                    if not title:
                        continue
                    
                    # Извлекаем ссылку
                    link = ""
                    link_elem = await result.query_selector('a')
                    if link_elem:
                        link = await link_elem.get_attribute('href')
                    
                    # Если ссылка не найдена, ищем в родительских элементах
                    if not link:
                        all_links = await result.query_selector_all('a')
                        for a in all_links:
                            href = await a.get_attribute('href')
                            if href and href.startswith('http') and 'google.com' not in href:
                                link = href
                                break
                    
                    if not link or not link.startswith('http'):
                        continue
                    
                    # Извлекаем описание (snippet)
                    snippet = ""
                    snippet_selectors = [
                        'div[data-sncf]',
                        'div.VwiC3b',
                        'span.aCOpRe',
                        'div[style*="line-height"]',
                        'div.s',
                        'span.st'
                    ]
                    
                    for sel in snippet_selectors:
                        snippet_elem = await result.query_selector(sel)
                        if snippet_elem:
                            snippet = await snippet_elem.inner_text()
                            if snippet:
                                break
                    
                    # Добавляем результат
                    results.append({
                        "title": title.strip(),
                        "link": link,
                        "snippet": snippet.strip()
                    })
                    
                except Exception as e:
                    # Игнорируем ошибки для отдельных результатов
                    continue
            
            # Если результатов все еще нет, делаем скриншот для отладки
            if not results:
                try:
                    await page.screenshot(path="debug_search_results.png")
                    page_content = await page.content()
                    # Сохраняем HTML для анализа
                    with open("debug_search_page.html", "w", encoding="utf-8") as f:
                        f.write(page_content)
                except:
                    pass
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
        else:
            return {"success": False, "error": "Не удалось найти поле поиска"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

async def browser_extract_content(url: str, selectors: list = None) -> Dict[str, Any]:
    """
    Извлекает текстовый контент со страницы по URL.
    Полезно для извлечения информации из результатов поиска.
    
    Args:
        url: URL страницы для извлечения контента
        selectors: Список CSS селекторов для извлечения (по умолчанию извлекает основной контент)
    
    Returns:
        Dict с успехом, URL, заголовком и извлеченным текстом
    """
    page = await _ensure_browser()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)
        
        title = await page.title()
        
        # Если селекторы не указаны, используем стандартные для основного контента
        if not selectors:
            selectors = [
                'article', 'main', '[role="main"]', 
                '.content', '#content', '.main-content',
                'body'
            ]
        
        extracted_text = ""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text) > 100:  # Берем первый значимый контент
                        extracted_text = text[:3000]  # Лимит для контекста
                        break
            except Exception:
                continue
        
        # Если ничего не нашли, берем весь body
        if not extracted_text:
            extracted_text = await page.inner_text('body')
            extracted_text = extracted_text[:3000]
        
        return {
            "success": True,
            "url": url,
            "title": title,
            "content": extracted_text,
            "content_length": len(extracted_text)
        }
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}

async def browser_close() -> Dict[str, Any]:
    """Закрывает браузер."""
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
    return {"success": True}
