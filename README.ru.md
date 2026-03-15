<p align="center">
  <img src="docs/assets/logo.png" alt="Skill Seekers" width="200"/>
</p>

# Skill Seekers

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Türkçe](README.tr.md) | [العربية](README.ar.md) | [हिन्दी](README.hi.md) | Русский

> ⚠️ **Уведомление о машинном переводе**
>
> Этот документ был автоматически переведён с помощью ИИ. Несмотря на наши усилия по обеспечению качества, возможны неточные выражения.

[![Версия](https://img.shields.io/badge/version-3.2.0-blue.svg)](https://github.com/yusufkaraaslan/Skill_Seekers/releases)
[![Лицензия: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP-интеграция](https://img.shields.io/badge/MCP-Integrated-blue.svg)](https://modelcontextprotocol.io)
[![Тесты пройдены](https://img.shields.io/badge/Tests-2540%2B%20Passing-brightgreen.svg)](tests/)
[![Доска проекта](https://img.shields.io/badge/Project-Board-purple.svg)](https://github.com/users/yusufkaraaslan/projects/2)
[![PyPI версия](https://badge.fury.io/py/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![PyPI - Загрузки](https://img.shields.io/pypi/dm/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![PyPI - Версия Python](https://img.shields.io/pypi/pyversions/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![Веб-сайт](https://img.shields.io/badge/Website-skillseekersweb.com-blue.svg)](https://skillseekersweb.com/)
[![Twitter](https://img.shields.io/twitter/follow/_yUSyUS_?style=social)](https://x.com/_yUSyUS_)
[![GitHub Stars](https://img.shields.io/github/stars/yusufkaraaslan/Skill_Seekers?style=social)](https://github.com/yusufkaraaslan/Skill_Seekers)

**🧠 Слой данных для ИИ-систем.** Skill Seekers преобразует документацию сайтов, репозитории GitHub, PDF, видео, Jupyter-ноутбуки, вики и более 17 типов источников в структурированные базы знаний — готовые к использованию в ИИ-навыках (Claude, Gemini, OpenAI), RAG-конвейерах (LangChain, LlamaIndex, Pinecone) и ИИ-помощниках для программирования (Cursor, Windsurf, Cline) за считанные минуты.

> 🌐 **[Посетите SkillSeekersWeb.com](https://skillseekersweb.com/)** — просматривайте 24+ готовых конфигураций, делитесь своими настройками и получайте доступ к полной документации!

> 📋 **[Смотрите дорожную карту разработки и задачи](https://github.com/users/yusufkaraaslan/projects/2)** — 134 задачи в 10 категориях, выберите любую для участия!

## 🧠 Слой данных для ИИ-систем

**Skill Seekers — это универсальный слой предобработки**, расположенный между необработанной документацией и всеми ИИ-системами, которые её потребляют. Независимо от того, создаёте ли вы навыки для Claude, RAG-конвейер LangChain или файл `.cursorrules` для Cursor — подготовка данных одинакова. Выполните её один раз и экспортируйте во все целевые платформы.

```bash
# Одна команда → структурированная база знаний
skill-seekers create https://docs.react.dev/
# или: skill-seekers create facebook/react
# или: skill-seekers create ./my-project

# Экспорт в любую ИИ-систему
skill-seekers package output/react --target claude      # → Claude AI навык (ZIP)
skill-seekers package output/react --target langchain   # → LangChain Documents
skill-seekers package output/react --target llama-index # → LlamaIndex TextNodes
skill-seekers package output/react --target cursor      # → .cursorrules
```

### Что создаётся

| Результат | Цель | Где используется |
|-----------|------|-----------------|
| **Claude навык** (ZIP + YAML) | `--target claude` | Claude Code, Claude API |
| **Gemini навык** (tar.gz) | `--target gemini` | Google Gemini |
| **OpenAI / Custom GPT** (ZIP) | `--target openai` | GPT-4o, пользовательские ассистенты |
| **LangChain Documents** | `--target langchain` | QA-цепочки, агенты, ретриверы |
| **LlamaIndex TextNodes** | `--target llama-index` | Движки запросов, движки диалогов |
| **Haystack Documents** | `--target haystack` | Корпоративные RAG-конвейеры |
| **Pinecone-ready** (Markdown) | `--target markdown` | Загрузка в векторное хранилище |
| **ChromaDB / FAISS / Qdrant** | `--format chroma/faiss/qdrant` | Локальные векторные базы данных |
| **Cursor** `.cursorrules` | `--target claude` → скопировать | Cursor IDE ИИ-контекст |
| **Windsurf / Cline / Continue** | `--target claude` → скопировать | VS Code, IntelliJ, Vim |

### Почему это важно

- ⚡ **На 99% быстрее** — дни ручной подготовки данных → 15–45 минут
- 🎯 **Качество ИИ-навыков** — файлы SKILL.md на 500+ строк с примерами, шаблонами и руководствами
- 📊 **Готовые к RAG блоки** — умная разбивка сохраняет блоки кода и контекст
- 🎬 **Видео** — извлечение кода, субтитров и структурированных знаний из YouTube и локальных видео
- 🔄 **Множество источников** — объединение 17 типов источников (документация, GitHub, PDF, видео, ноутбуки, вики и другие) в единую базу знаний
- 🌐 **Одна подготовка — все платформы** — экспорт одного актива на 16 платформ без повторного сканирования
- ✅ **Проверено в бою** — 2 540+ тестов, 24+ пресетов для фреймворков, готово к продакшену

## Быстрый старт

```bash
pip install skill-seekers

# Создание ИИ-навыка из любого источника
skill-seekers create https://docs.django.com/    # Документация сайта
skill-seekers create django/django               # Репозиторий GitHub
skill-seekers create ./my-codebase               # Локальный проект
skill-seekers create manual.pdf                  # PDF-файл
skill-seekers create manual.docx                 # Документ Word
skill-seekers create book.epub                   # Электронная книга EPUB
skill-seekers create notebook.ipynb              # Jupyter-ноутбук
skill-seekers create page.html                   # Локальный HTML
skill-seekers create api-spec.yaml               # Спецификация OpenAPI/Swagger
skill-seekers create guide.adoc                  # Документ AsciiDoc
skill-seekers create slides.pptx                 # Презентация PowerPoint

# Видео (YouTube, Vimeo или локальный файл — требуется skill-seekers[video])
skill-seekers video --url https://www.youtube.com/watch?v=... --name mytutorial
# Первый запуск? Автоматическая установка зависимостей с поддержкой GPU:
skill-seekers video --setup

# Экспорт по назначению
skill-seekers package output/django --target claude     # Claude AI навык
skill-seekers package output/django --target langchain  # LangChain RAG
skill-seekers package output/django --target cursor     # Cursor IDE контекст
```

**Полные примеры:**
- [Claude AI навык](examples/claude-skill/) — навык для Claude Code
- [LangChain RAG-конвейер](examples/langchain-rag-pipeline/) — QA-цепочка на основе Chroma
- [Cursor IDE контекст](examples/cursor-react-skill/) — ИИ-программирование с учётом фреймворка

## Что такое Skill Seekers?

Skill Seekers — это **слой данных для ИИ-систем**, который преобразует 17 типов источников — документацию сайтов, репозитории GitHub, PDF, видео, Jupyter-ноутбуки, документы Word/EPUB/AsciiDoc, спецификации OpenAPI/Swagger, презентации PowerPoint, RSS/Atom-ленты, man-страницы, вики Confluence, страницы Notion, экспорты Slack/Discord и другое — в структурированные базы знаний для всех ИИ-целей:

| Сценарий использования | Что вы получаете | Примеры |
|----------------------|-----------------|---------|
| **ИИ-навыки** | Полный SKILL.md + справочные файлы | Claude Code, Gemini, GPT |
| **RAG-конвейеры** | Документы, разбитые на блоки с метаданными | LangChain, LlamaIndex, Haystack |
| **Векторные базы данных** | Предварительно отформатированные данные для загрузки | Pinecone, Chroma, Weaviate, FAISS |
| **ИИ-помощники для кода** | Файлы контекста, которые IDE-ИИ читает автоматически | Cursor, Windsurf, Cline, Continue.dev |

Skill Seekers заменяет дни ручной предобработки следующими шагами:

1. **Сбор** — документация, репозитории GitHub, локальные кодовые базы, PDF, видео, Jupyter-ноутбуки, вики и более 17 типов источников
2. **Анализ** — глубокий AST-разбор, обнаружение паттернов, извлечение API
3. **Структурирование** — категоризированные справочные файлы с метаданными
4. **Улучшение** — генерация SKILL.md с помощью ИИ (Claude, Gemini или локально)
5. **Экспорт** — 16 платформоспецифичных форматов из одного актива

## Зачем использовать Skill Seekers?

### Для создателей ИИ-навыков (Claude, Gemini, OpenAI)

- 🎯 **Навыки продакшен-уровня** — файлы SKILL.md на 500+ строк с примерами кода, шаблонами и руководствами
- 🔄 **Рабочие процессы улучшения** — применяйте `security-focus`, `architecture-comprehensive` или пользовательские YAML-пресеты
- 🎮 **Любая предметная область** — игровые движки (Godot, Unity), фреймворки (React, Django), внутренние инструменты
- 🔧 **Командная работа** — объединяйте внутреннюю документацию + код в единый источник истины
- 📚 **Качество** — ИИ-улучшение с примерами, кратким справочником и навигацией

### Для RAG-разработчиков и ИИ-инженеров

- 🤖 **Данные, готовые к RAG** — предварительно разбитые LangChain `Documents`, LlamaIndex `TextNodes`, Haystack `Documents`
- 🚀 **На 99% быстрее** — дни предобработки → 15–45 минут
- 📊 **Умные метаданные** — категории, источники, типы → более точный поиск
- 🔄 **Множество источников** — объединяйте документацию + GitHub + PDF в одном конвейере
- 🌐 **Платформонезависимость** — экспорт в любую векторную базу данных или фреймворк без повторного сканирования

### Для пользователей ИИ-помощников для программирования

- 💻 **Cursor / Windsurf / Cline** — автоматическая генерация `.cursorrules` / `.windsurfrules` / `.clinerules`
- 🎯 **Постоянный контекст** — ИИ «знает» ваши фреймворки без повторных подсказок
- 📚 **Всегда актуально** — обновляйте контекст за минуты при изменении документации

## Ключевые возможности

### 🌐 Сканирование документации
- ✅ **Поддержка llms.txt** — автоматическое обнаружение и использование LLM-ready файлов документации (в 10 раз быстрее)
- ✅ **Универсальный сканер** — работает с ЛЮБЫМ сайтом документации
- ✅ **Умная категоризация** — автоматическая организация контента по темам
- ✅ **Определение языка кода** — распознавание Python, JavaScript, C++, GDScript и других
- ✅ **24+ готовых пресетов** — Godot, React, Vue, Django, FastAPI и другие

### 📄 Поддержка PDF
- ✅ **Базовое извлечение PDF** — извлечение текста, кода и изображений из PDF-файлов
- ✅ **OCR для сканированных PDF** — извлечение текста из сканированных документов
- ✅ **PDF с паролем** — обработка зашифрованных PDF
- ✅ **Извлечение таблиц** — извлечение сложных таблиц из PDF
- ✅ **Параллельная обработка** — в 3 раза быстрее для больших PDF
- ✅ **Умное кэширование** — на 50% быстрее при повторных запусках

### 🎬 Извлечение из видео
- ✅ **YouTube и локальные видео** — извлечение субтитров, кода и структурированных знаний из видео
- ✅ **Анализ визуальных кадров** — OCR-извлечение из редакторов кода, терминалов, слайдов и диаграмм
- ✅ **Автоопределение GPU** — автоматическая установка правильной сборки PyTorch (CUDA/ROCm/MPS/CPU)
- ✅ **ИИ-улучшение** — двухэтапное: очистка артефактов OCR + генерация отполированного SKILL.md
- ✅ **Обрезка по времени** — извлечение определённых фрагментов с `--start-time` и `--end-time`
- ✅ **Поддержка плейлистов** — пакетная обработка всех видео в плейлисте YouTube

### 🐙 Анализ репозиториев GitHub
- ✅ **Глубокий анализ кода** — AST-разбор для Python, JavaScript, TypeScript, Java, C++, Go
- ✅ **Извлечение API** — функции, классы, методы с параметрами и типами
- ✅ **Метаданные репозитория** — README, дерево файлов, распределение языков, звёзды/форки
- ✅ **GitHub Issues и PR** — получение открытых/закрытых issues с метками и вехами
- ✅ **CHANGELOG и релизы** — автоматическое извлечение истории версий
- ✅ **Обнаружение конфликтов** — сравнение документированных API с фактической реализацией кода
- ✅ **MCP-интеграция** — на естественном языке: «Просканируй GitHub-репозиторий facebook/react»

### 🔄 Унифицированное мультиисточниковое сканирование
- ✅ **Объединение нескольких источников** — смешивайте документацию + GitHub + PDF в одном навыке
- ✅ **Обнаружение конфликтов** — автоматическое нахождение расхождений между документацией и кодом
- ✅ **Умное слияние** — на основе правил или с помощью ИИ
- ✅ **Прозрачная отчётность** — сравнение бок о бок с предупреждениями ⚠️
- ✅ **Анализ пробелов в документации** — выявление устаревшей документации и недокументированных функций
- ✅ **Единый источник истины** — один навык показывает и намерение (документация), и реальность (код)
- ✅ **Обратная совместимость** — устаревшие одноисточниковые конфигурации продолжают работать

### 🤖 Поддержка нескольких LLM-платформ
- ✅ **4 LLM-платформы** — Claude AI, Google Gemini, OpenAI ChatGPT, универсальный Markdown
- ✅ **Универсальное сканирование** — одна и та же документация для всех платформ
- ✅ **Платформоспецифичная упаковка** — оптимизированные форматы для каждой LLM
- ✅ **Экспорт одной командой** — флаг `--target` для выбора платформы
- ✅ **Опциональные зависимости** — устанавливайте только то, что нужно
- ✅ **100% обратная совместимость** — существующие рабочие процессы Claude без изменений

| Платформа | Формат | Загрузка | Улучшение | API Key | Пользовательский эндпоинт |
|-----------|--------|----------|-----------|---------|--------------------------|
| **Claude AI** | ZIP + YAML | ✅ Авто | ✅ Да | ANTHROPIC_API_KEY | ANTHROPIC_BASE_URL |
| **Google Gemini** | tar.gz | ✅ Авто | ✅ Да | GOOGLE_API_KEY | - |
| **OpenAI ChatGPT** | ZIP + Vector Store | ✅ Авто | ✅ Да | OPENAI_API_KEY | - |
| **Универсальный Markdown** | ZIP | ❌ Вручную | ❌ Нет | - | - |

```bash
# Claude (по умолчанию — без изменений!)
skill-seekers package output/react/
skill-seekers upload react.zip

# Google Gemini
pip install skill-seekers[gemini]
skill-seekers package output/react/ --target gemini
skill-seekers upload react-gemini.tar.gz --target gemini

# OpenAI ChatGPT
pip install skill-seekers[openai]
skill-seekers package output/react/ --target openai
skill-seekers upload react-openai.zip --target openai

# Универсальный Markdown (универсальный экспорт)
skill-seekers package output/react/ --target markdown
```

<details>
<summary>🔧 <strong>Переменные окружения для Claude-совместимых API (например, GLM-4.7)</strong></summary>

Skill Seekers поддерживает любой Claude-совместимый API-эндпоинт:

```bash
# Вариант 1: Официальный Anthropic API (по умолчанию)
export ANTHROPIC_API_KEY=sk-ant-...

# Вариант 2: GLM-4.7 Claude-совместимый API
export ANTHROPIC_API_KEY=your-glm-47-api-key
export ANTHROPIC_BASE_URL=https://glm-4-7-endpoint.com/v1

# Все функции ИИ-улучшения будут использовать настроенный эндпоинт
skill-seekers enhance output/react/
skill-seekers analyze --directory . --enhance
```

**Примечание**: Установка `ANTHROPIC_BASE_URL` позволяет использовать любой Claude-совместимый API-эндпоинт, например GLM-4.7 или другие совместимые сервисы.

</details>

**Установка:**
```bash
# Установка с поддержкой Gemini
pip install skill-seekers[gemini]

# Установка с поддержкой OpenAI
pip install skill-seekers[openai]

# Установка всех LLM-платформ
pip install skill-seekers[all-llms]
```

### 🔗 Интеграции с RAG-фреймворками

- ✅ **LangChain Documents** — прямой экспорт в формат `Document` с `page_content` + метаданными
  - Подходит для: QA-цепочек, ретриверов, векторных хранилищ, агентов
  - Пример: [LangChain RAG-конвейер](examples/langchain-rag-pipeline/)
  - Руководство: [Интеграция с LangChain](docs/integrations/LANGCHAIN.md)

- ✅ **LlamaIndex TextNodes** — экспорт в формат `TextNode` с уникальными ID + эмбеддингами
  - Подходит для: движков запросов, движков диалогов, контекста хранилища
  - Пример: [LlamaIndex движок запросов](examples/llama-index-query-engine/)
  - Руководство: [Интеграция с LlamaIndex](docs/integrations/LLAMA_INDEX.md)

- ✅ **Формат, готовый к Pinecone** — оптимизирован для загрузки в векторную базу данных
  - Подходит для: продакшен-поиска по векторам, семантического и гибридного поиска
  - Пример: [Загрузка в Pinecone](examples/pinecone-upsert/)
  - Руководство: [Интеграция с Pinecone](docs/integrations/PINECONE.md)

**Быстрый экспорт:**
```bash
# LangChain Documents (JSON)
skill-seekers package output/django --target langchain
# → output/django-langchain.json

# LlamaIndex TextNodes (JSON)
skill-seekers package output/django --target llama-index
# → output/django-llama-index.json

# Markdown (универсальный)
skill-seekers package output/django --target markdown
# → output/django-markdown/SKILL.md + references/
```

**Полное руководство по RAG-конвейерам:** [Документация по RAG-конвейерам](docs/integrations/RAG_PIPELINES.md)

---

### 🧠 Интеграции с ИИ-помощниками для программирования

Преобразуйте документацию любого фреймворка в экспертный контекст для 4+ ИИ-помощников:

- ✅ **Cursor IDE** — генерация `.cursorrules` для ИИ-подсказок при написании кода
  - Подходит для: генерации кода с учётом фреймворка, единообразных паттернов
  - Руководство: [Интеграция с Cursor](docs/integrations/CURSOR.md)
  - Пример: [Cursor React навык](examples/cursor-react-skill/)

- ✅ **Windsurf** — настройка контекста ИИ-помощника Windsurf через `.windsurfrules`
  - Подходит для: встроенной ИИ-помощи в IDE, потоковое программирование
  - Руководство: [Интеграция с Windsurf](docs/integrations/WINDSURF.md)
  - Пример: [Windsurf FastAPI контекст](examples/windsurf-fastapi-context/)

- ✅ **Cline (VS Code)** — системные промпты + MCP для VS Code-агента
  - Подходит для: автономной генерации кода в VS Code
  - Руководство: [Интеграция с Cline](docs/integrations/CLINE.md)
  - Пример: [Cline Django ассистент](examples/cline-django-assistant/)

- ✅ **Continue.dev** — контекстные серверы для IDE-независимого ИИ
  - Подходит для: мультисредных окружений (VS Code, JetBrains, Vim), пользовательских LLM-провайдеров
  - Руководство: [Интеграция с Continue](docs/integrations/CONTINUE_DEV.md)
  - Пример: [Continue универсальный контекст](examples/continue-dev-universal/)

**Быстрый экспорт для ИИ-инструментов программирования:**
```bash
# Для любого ИИ-помощника (Cursor, Windsurf, Cline, Continue.dev)
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target claude

# Скопируйте в свой проект (пример для Cursor)
cp output/django-claude/SKILL.md my-project/.cursorrules

# Или для Windsurf
cp output/django-claude/SKILL.md my-project/.windsurf/rules/django.md

# Или для Cline
cp output/django-claude/SKILL.md my-project/.clinerules
```

**Центр интеграций:** [Все интеграции с ИИ-системами](docs/integrations/INTEGRATIONS.md)

---

### 🌊 Трёхпоточная архитектура GitHub
- ✅ **Трёхпоточный анализ** — разделение GitHub-репозитория на потоки «Код», «Документация» и «Аналитика»
- ✅ **Унифицированный анализатор кодовой базы** — работает как с URL GitHub, так и с локальными путями
- ✅ **C3.x как глубина анализа** — выбор «basic» (1–2 мин) или «c3x» (20–60 мин)
- ✅ **Расширенная генерация маршрутизатора** — метаданные GitHub, быстрый старт из README, типичные проблемы
- ✅ **Интеграция Issues** — распространённые проблемы и решения из GitHub Issues
- ✅ **Умные ключевые слова маршрутизации** — метки GitHub с двойным весом для лучшего определения тем

**Описание трёх потоков:**
- **Поток 1: Код** — глубокий C3.x-анализ (паттерны, примеры, руководства, конфигурации, архитектура)
- **Поток 2: Документация** — документация репозитория (README, CONTRIBUTING, docs/*.md)
- **Поток 3: Аналитика** — знания сообщества (Issues, метки, звёзды, форки)

```python
from skill_seekers.cli.unified_codebase_analyzer import UnifiedCodebaseAnalyzer

# Анализ GitHub-репозитория со всеми тремя потоками
analyzer = UnifiedCodebaseAnalyzer()
result = analyzer.analyze(
    source="https://github.com/facebook/react",
    depth="c3x",  # или "basic" для быстрого анализа
    fetch_github_metadata=True
)

print(f"Паттерны проектирования: {len(result.code_analysis['c3_1_patterns'])}")
print(f"Звёзды: {result.github_insights['metadata']['stars']}")
```

**Полная документация**: [Сводка по реализации трёхпоточной архитектуры](docs/IMPLEMENTATION_SUMMARY_THREE_STREAM.md)

### 🔐 Умное управление лимитами запросов и конфигурация
- ✅ **Система конфигурации с несколькими токенами** — управление несколькими аккаунтами GitHub (личный, рабочий, open source)
  - Безопасное хранение конфигурации в `~/.config/skill-seekers/config.json` (права 600)
  - Стратегии лимита запросов для каждого профиля: `prompt`, `wait`, `switch`, `fail`
  - Умная цепочка резервирования: аргумент CLI → переменная окружения → файл конфигурации → запрос
- ✅ **Интерактивный мастер настройки** — красивый терминальный интерфейс для простой настройки
- ✅ **Умный обработчик лимитов запросов** — больше никаких бесконечных ожиданий!
  - Обратный отсчёт в реальном времени, автоматическое переключение профилей
  - Четыре стратегии: prompt (спросить), wait (обратный отсчёт), switch (переключить), fail (прервать)
- ✅ **Возобновление** — продолжение прерванных задач
- ✅ **Поддержка CI/CD** — флаг `--non-interactive` для автоматизации

**Быстрая настройка:**
```bash
# Однократная настройка (5 минут)
skill-seekers config --github

# Использование определённого профиля для приватных репозиториев
skill-seekers github --repo mycompany/private-repo --profile work

# Режим CI/CD (быстрый отказ, без запросов)
skill-seekers github --repo owner/repo --non-interactive
```

### 🎯 Bootstrap-навык — самохостинг

Генерация skill-seekers как навыка для Claude Code:

```bash
./scripts/bootstrap_skill.sh
cp -r output/skill-seekers ~/.claude/skills/
```

### 🔐 Приватные репозитории конфигураций
- ✅ **Git-источники конфигураций** — получение конфигураций из приватных/командных Git-репозиториев
- ✅ **Управление несколькими источниками** — регистрация неограниченного количества репозиториев GitHub, GitLab, Bitbucket
- ✅ **Командная работа** — обмен пользовательскими конфигурациями в командах из 3–5 человек
- ✅ **Корпоративная поддержка** — масштабирование до 500+ разработчиков
- ✅ **Безопасная аутентификация** — токены через переменные окружения (GITHUB_TOKEN, GITLAB_TOKEN)

### 🤖 Анализ кодовой базы (C3.x)

**C3.4: Извлечение паттернов конфигурации с ИИ-улучшением**
- ✅ **9 форматов конфигурации** — JSON, YAML, TOML, ENV, INI, Python, JavaScript, Dockerfile, Docker Compose
- ✅ **7 типов паттернов** — база данных, API, логирование, кэш, почта, аутентификация, сервер
- ✅ **ИИ-улучшение** — опциональный двухрежимный ИИ-анализ (API + LOCAL)
- ✅ **Анализ безопасности** — обнаружение жёстко закодированных секретов и открытых учётных данных

**C3.3: ИИ-улучшенные пошаговые руководства**
- ✅ **Полное ИИ-улучшение** — преобразование базовых руководств в профессиональные учебники
- ✅ **5 автоматических улучшений** — описание шагов, устранение неполадок, предварительные требования, следующие шаги, сценарии использования
- ✅ **Двухрежимная поддержка** — API-режим (Claude API) или LOCAL-режим (Claude Code CLI)
- ✅ **Нулевые затраты в LOCAL-режиме** — БЕСПЛАТНОЕ улучшение с вашим планом Claude Code Max

**Использование:**
```bash
# Быстрый анализ (1–2 мин, только базовые функции)
skill-seekers analyze --directory tests/ --quick

# Комплексный анализ (с ИИ, 20–60 мин)
skill-seekers analyze --directory tests/ --comprehensive

# С ИИ-улучшением
skill-seekers analyze --directory tests/ --enhance
```

**Полная документация:** [docs/HOW_TO_GUIDES.md](docs/HOW_TO_GUIDES.md#ai-enhancement-new)

### 🔄 Пресеты рабочих процессов улучшения

Многоразовые YAML-определённые конвейеры улучшения, управляющие тем, как ИИ преобразует необработанную документацию в отшлифованный навык.

- ✅ **5 встроенных пресетов** — `default`, `minimal`, `security-focus`, `architecture-comprehensive`, `api-documentation`
- ✅ **Пользовательские пресеты** — добавляйте собственные рабочие процессы в `~/.config/skill-seekers/workflows/`
- ✅ **Цепочки рабочих процессов** — объединяйте два или более рабочих процесса в одной команде
- ✅ **Полное управление через CLI** — просмотр, копирование, добавление, удаление и валидация рабочих процессов

```bash
# Применение одного рабочего процесса
skill-seekers create ./my-project --enhance-workflow security-focus

# Цепочка нескольких рабочих процессов (применяются по порядку)
skill-seekers create ./my-project \
  --enhance-workflow security-focus \
  --enhance-workflow minimal

# Управление пресетами
skill-seekers workflows list                          # Список всех (встроенные + пользовательские)
skill-seekers workflows show security-focus           # Показать содержимое YAML
skill-seekers workflows copy security-focus           # Скопировать в пользовательскую директорию для редактирования
skill-seekers workflows add ./my-workflow.yaml        # Установить пользовательский пресет
skill-seekers workflows remove my-workflow            # Удалить пользовательский пресет
skill-seekers workflows validate security-focus       # Проверить структуру пресета

# Копирование нескольких сразу
skill-seekers workflows copy security-focus minimal api-documentation

# Добавление нескольких файлов сразу
skill-seekers workflows add ./wf-a.yaml ./wf-b.yaml

# Удаление нескольких сразу
skill-seekers workflows remove my-wf-a my-wf-b
```

**Формат YAML-пресета:**
```yaml
name: security-focus
description: "Обзор безопасности: уязвимости, аутентификация, обработка данных"
version: "1.0"
stages:
  - name: vulnerabilities
    type: custom
    prompt: "Проверить на OWASP Top 10 и распространённые уязвимости..."
  - name: auth-review
    type: custom
    prompt: "Исследовать паттерны аутентификации и авторизации..."
    uses_history: true
```

### ⚡ Производительность и масштаб
- ✅ **Асинхронный режим** — сканирование в 2–3 раза быстрее с async/await (флаг `--async`)
- ✅ **Поддержка большой документации** — обработка документов на 10K–40K+ страниц с умным разделением
- ✅ **Маршрутизатор/Hub-навыки** — интеллектуальная маршрутизация к специализированным поднавыкам
- ✅ **Параллельное сканирование** — одновременная обработка нескольких навыков
- ✅ **Контрольные точки/Возобновление** — прогресс никогда не теряется при длительном сканировании
- ✅ **Система кэширования** — сканируйте один раз, пересобирайте мгновенно

### ✅ Контроль качества
- ✅ **Полное покрытие тестами** — 2 540+ тестов с обширным покрытием

---

## 📦 Установка

```bash
# Базовая установка (сканирование документации, анализ GitHub, PDF, упаковка)
pip install skill-seekers

# С поддержкой всех LLM-платформ
pip install skill-seekers[all-llms]

# С MCP-сервером
pip install skill-seekers[mcp]

# Всё включено
pip install skill-seekers[all]
```

**Нужна помощь с выбором?** Запустите мастер настройки:
```bash
skill-seekers-setup
```

### Варианты установки

| Команда установки | Функциональность |
|-------------------|-----------------|
| `pip install skill-seekers` | Сканирование, анализ GitHub, PDF, все платформы |
| `pip install skill-seekers[gemini]` | + Поддержка Google Gemini |
| `pip install skill-seekers[openai]` | + Поддержка OpenAI ChatGPT |
| `pip install skill-seekers[all-llms]` | + Все LLM-платформы |
| `pip install skill-seekers[mcp]` | + MCP-сервер |
| `pip install skill-seekers[video]` | + Извлечение субтитров и метаданных YouTube/Vimeo |
| `pip install skill-seekers[video-full]` | + Транскрипция Whisper и извлечение визуальных кадров |
| `pip install skill-seekers[jupyter]` | + Поддержка Jupyter-ноутбуков |
| `pip install skill-seekers[pptx]` | + Поддержка PowerPoint |
| `pip install skill-seekers[confluence]` | + Поддержка вики Confluence |
| `pip install skill-seekers[notion]` | + Поддержка страниц Notion |
| `pip install skill-seekers[rss]` | + Поддержка RSS/Atom-лент |
| `pip install skill-seekers[chat]` | + Поддержка экспорта чатов Slack/Discord |
| `pip install skill-seekers[asciidoc]` | + Поддержка документов AsciiDoc |
| `pip install skill-seekers[all]` | Всё включено |

> **Визуальные зависимости для видео (с поддержкой GPU):** После установки `skill-seekers[video-full]` запустите
> `skill-seekers video --setup` для автоопределения вашего GPU и установки правильной сборки PyTorch
> + easyocr. Это рекомендуемый способ установки зависимостей для визуального извлечения.

---

## 🚀 Рабочий процесс установки одной командой

**Самый быстрый способ от конфигурации до загруженного навыка — полная автоматизация:**

```bash
# Установка навыка React из официальных конфигураций (автозагрузка в Claude)
skill-seekers install --config react

# Установка из локального файла конфигурации
skill-seekers install --config configs/custom.json

# Установка без загрузки (только упаковка)
skill-seekers install --config django --no-upload

# Предпросмотр рабочего процесса без выполнения
skill-seekers install --config react --dry-run
```

**Выполняемые фазы:**
```
📥 ФАЗА 1: Получение конфигурации (если указано имя конфигурации)
📖 ФАЗА 2: Сканирование документации
✨ ФАЗА 3: ИИ-улучшение
📦 ФАЗА 4: Упаковка навыка
☁️  ФАЗА 5: Загрузка в Claude (опционально, требуется API Key)
```

---

## 📊 Матрица функций

Skill Seekers поддерживает **4 LLM-платформы**, **17 типов источников** и полный паритет функций по всем целевым платформам.

**Платформы:** Claude AI, Google Gemini, OpenAI ChatGPT, универсальный Markdown
**Типы источников:** Документация сайтов, репозитории GitHub, PDF, Word (.docx), EPUB, видео, локальные кодовые базы, Jupyter-ноутбуки, локальный HTML, OpenAPI/Swagger, AsciiDoc, PowerPoint (.pptx), RSS/Atom-ленты, man-страницы, вики Confluence, страницы Notion, экспорты чатов Slack/Discord

Подробности см. в [Полной матрице функций](docs/FEATURE_MATRIX.md).

### Быстрое сравнение платформ

| Функция | Claude | Gemini | OpenAI | Markdown |
|---------|--------|--------|--------|----------|
| Формат | ZIP + YAML | tar.gz | ZIP + Vector | ZIP |
| Загрузка | ✅ API | ✅ API | ✅ API | ❌ Вручную |
| Улучшение | ✅ Sonnet 4 | ✅ 2.0 Flash | ✅ GPT-4o | ❌ Нет |
| Все режимы навыков | ✅ | ✅ | ✅ | ✅ |

---

## Примеры использования

### Сканирование документации

```bash
# Сканирование документации сайта
skill-seekers scrape --config configs/react.json

# Быстрое сканирование без конфигурации
skill-seekers scrape --url https://react.dev --name react

# Асинхронный режим (в 3 раза быстрее)
skill-seekers scrape --config configs/godot.json --async --workers 8
```

### Извлечение из PDF

```bash
# Базовое извлечение из PDF
skill-seekers pdf --pdf docs/manual.pdf --name myskill

# Расширенные функции
skill-seekers pdf --pdf docs/manual.pdf --name myskill \
    --extract-tables \        # Извлечение таблиц
    --parallel \              # Быстрая параллельная обработка
    --workers 8               # Использование 8 ядер CPU

# Сканированные PDF (требуется: pip install pytesseract Pillow)
skill-seekers pdf --pdf docs/scanned.pdf --name myskill --ocr
```

### Извлечение из видео

```bash
# Установка поддержки видео
pip install skill-seekers[video]        # Субтитры + метаданные
pip install skill-seekers[video-full]   # + Whisper транскрипция + извлечение визуальных кадров

# Автоопределение GPU и установка визуальных зависимостей (PyTorch + easyocr)
skill-seekers video --setup

# Извлечение из видео YouTube
skill-seekers video --url https://www.youtube.com/watch?v=dQw4w9WgXcQ --name mytutorial

# Извлечение из плейлиста YouTube
skill-seekers video --playlist https://www.youtube.com/playlist?list=... --name myplaylist

# Извлечение из локального видеофайла
skill-seekers video --video-file recording.mp4 --name myrecording

# Извлечение с анализом визуальных кадров (требуются зависимости video-full)
skill-seekers video --url https://www.youtube.com/watch?v=... --name mytutorial --visual

# С ИИ-улучшением (очистка OCR + генерация отполированного SKILL.md)
skill-seekers video --url https://www.youtube.com/watch?v=... --visual --enhance-level 2

# Обрезка определённого фрагмента видео (поддерживаются секунды, MM:SS, HH:MM:SS)
skill-seekers video --url https://www.youtube.com/watch?v=... --start-time 1:30 --end-time 5:00

# Использование Vision API для OCR-кадров с низкой достоверностью (требуется ANTHROPIC_API_KEY)
skill-seekers video --url https://www.youtube.com/watch?v=... --visual --vision-ocr

# Пересборка навыка из ранее извлечённых данных (пропуск загрузки)
skill-seekers video --from-json output/mytutorial/video_data/extracted_data.json --name mytutorial
```

> **Полное руководство:** см. [docs/VIDEO_GUIDE.md](docs/VIDEO_GUIDE.md) для полной справки по CLI,
> деталей визуального конвейера, опций ИИ-улучшения и устранения неполадок.

### Анализ репозиториев GitHub

```bash
# Базовое сканирование репозитория
skill-seekers github --repo facebook/react

# С аутентификацией (более высокие лимиты запросов)
export GITHUB_TOKEN=ghp_your_token_here
skill-seekers github --repo facebook/react

# Настройка содержимого
skill-seekers github --repo django/django \
    --include-issues \        # Извлечение GitHub Issues
    --max-issues 100 \        # Ограничение количества issues
    --include-changelog       # Извлечение CHANGELOG.md
```

### Унифицированное мультиисточниковое сканирование

**Объединение документации + GitHub + PDF в один навык с обнаружением конфликтов:**

```bash
# Использование готовых унифицированных конфигураций
skill-seekers unified --config configs/react_unified.json

# Или создание унифицированной конфигурации
cat > configs/myframework_unified.json << 'EOF'
{
  "name": "myframework",
  "merge_mode": "rule-based",
  "sources": [
    {
      "type": "documentation",
      "base_url": "https://docs.myframework.com/",
      "max_pages": 200
    },
    {
      "type": "github",
      "repo": "owner/myframework",
      "code_analysis_depth": "surface"
    }
  ]
}
EOF

skill-seekers unified --config configs/myframework_unified.json
```

**Обнаружение конфликтов автоматически находит:**
- 🔴 **Отсутствует в коде** (высокий приоритет): задокументировано, но не реализовано
- 🟡 **Отсутствует в документации** (средний приоритет): реализовано, но не задокументировано
- ⚠️ **Несовпадение сигнатур**: различные параметры/типы
- ℹ️ **Несовпадение описаний**: различные пояснения

**Полное руководство:** см. [docs/UNIFIED_SCRAPING.md](docs/UNIFIED_SCRAPING.md).

### Приватные репозитории конфигураций

**Обмен пользовательскими конфигурациями в команде через приватные Git-репозитории:**

```bash
# Использование MCP-инструментов для регистрации приватного командного репозитория
add_config_source(
    name="team",
    git_url="https://github.com/mycompany/skill-configs.git",
    token_env="GITHUB_TOKEN"
)

# Получение конфигурации из командного репозитория
fetch_config(source="team", config_name="internal-api")
```

**Поддерживаемые платформы:**
- GitHub (`GITHUB_TOKEN`), GitLab (`GITLAB_TOKEN`), Gitea (`GITEA_TOKEN`), Bitbucket (`BITBUCKET_TOKEN`)

**Полное руководство:** см. [docs/GIT_CONFIG_SOURCES.md](docs/GIT_CONFIG_SOURCES.md).

## Как это работает

```mermaid
graph LR
    A[Документация сайта] --> B[Skill Seekers]
    B --> C[Сканер]
    B --> D[ИИ-улучшение]
    B --> E[Упаковщик]
    C --> F[Организованные справочные файлы]
    D --> F
    F --> E
    E --> G[Claude навык .zip]
    G --> H[Загрузка в Claude AI]
```

0. **Обнаружение llms.txt** — проверка наличия llms-full.txt, llms.txt, llms-small.txt
1. **Сканирование**: извлечение всех страниц из документации
2. **Категоризация**: организация контента по темам (API, руководства, учебники и т.д.)
3. **Улучшение**: ИИ анализирует документацию и создаёт всеобъемлющий SKILL.md с примерами
4. **Упаковка**: объединение всего в готовый для Claude `.zip`-файл

## 📋 Предварительные требования

**Перед началом убедитесь, что у вас есть:**

1. **Python 3.10 или выше** — [Скачать](https://www.python.org/downloads/) | Проверить: `python3 --version`
2. **Git** — [Скачать](https://git-scm.com/) | Проверить: `git --version`
3. **15–30 минут** для первоначальной настройки

**Впервые?** → **[Начните здесь: Безотказное руководство быстрого старта](BULLETPROOF_QUICKSTART.md)** 🎯

---

## 📤 Загрузка навыков в Claude

После упаковки навыка его необходимо загрузить в Claude:

### Вариант 1: Автоматическая загрузка (через API)

```bash
# Установка API Key (однократно)
export ANTHROPIC_API_KEY=sk-ant-...

# Упаковка и автоматическая загрузка
skill-seekers package output/react/ --upload

# ИЛИ загрузка существующего .zip
skill-seekers upload output/react.zip
```

### Вариант 2: Ручная загрузка (без API Key)

```bash
# Упаковка навыка
skill-seekers package output/react/
# → Создаёт output/react.zip

# Затем загрузите вручную:
# - Перейдите на https://claude.ai/skills
# - Нажмите «Upload Skill»
# - Выберите output/react.zip
```

### Вариант 3: MCP (Claude Code)

```
В Claude Code просто попросите:
"Упакуй и загрузи навык React"
```

---

## 🤖 Установка в ИИ-агенты

Skill Seekers может автоматически устанавливать навыки в 10+ ИИ-агентов для программирования.

```bash
# Установка в конкретный агент
skill-seekers install-agent output/react/ --agent cursor

# Установка во все агенты сразу
skill-seekers install-agent output/react/ --agent all

# Предпросмотр без установки
skill-seekers install-agent output/react/ --agent cursor --dry-run
```

### Поддерживаемые агенты

| Агент | Путь | Тип |
|-------|------|-----|
| **Claude Code** | `~/.claude/skills/` | Глобальный |
| **Cursor** | `.cursor/skills/` | Проектный |
| **VS Code / Copilot** | `.github/skills/` | Проектный |
| **Amp** | `~/.amp/skills/` | Глобальный |
| **Goose** | `~/.config/goose/skills/` | Глобальный |
| **OpenCode** | `~/.opencode/skills/` | Глобальный |
| **Windsurf** | `~/.windsurf/skills/` | Глобальный |

---

## 🔌 MCP-интеграция (26 инструментов)

Skill Seekers поставляется с MCP-сервером для использования из Claude Code, Cursor, Windsurf, VS Code + Cline или IntelliJ IDEA.

```bash
# Режим stdio (Claude Code, VS Code + Cline)
python -m skill_seekers.mcp.server_fastmcp

# Режим HTTP (Cursor, Windsurf, IntelliJ)
python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765

# Автоматическая настройка всех агентов за раз
./setup_mcp.sh
```

**Все 26 инструментов:**
- **Основные (9):** `list_configs`, `generate_config`, `validate_config`, `estimate_pages`, `scrape_docs`, `package_skill`, `upload_skill`, `enhance_skill`, `install_skill`
- **Расширенные (10):** `scrape_github`, `scrape_pdf`, `unified_scrape`, `merge_sources`, `detect_conflicts`, `add_config_source`, `fetch_config`, `list_config_sources`, `remove_config_source`, `split_config`
- **Векторные БД (4):** `export_to_chroma`, `export_to_weaviate`, `export_to_faiss`, `export_to_qdrant`
- **Облачные (3):** `cloud_upload`, `cloud_download`, `cloud_list`

**Полное руководство:** [docs/MCP_SETUP.md](docs/MCP_SETUP.md)

---

## ⚙️ Конфигурация

### Доступные пресеты (24+)

```bash
# Список всех пресетов
skill-seekers list-configs
```

| Категория | Пресеты |
|-----------|---------|
| **Веб-фреймворки** | `react`, `vue`, `angular`, `svelte`, `nextjs` |
| **Python** | `django`, `flask`, `fastapi`, `sqlalchemy`, `pytest` |
| **Разработка игр** | `godot`, `pygame`, `unity` |
| **Инструменты и DevOps** | `docker`, `kubernetes`, `terraform`, `ansible` |
| **Унифицированные (документация + GitHub)** | `react-unified`, `vue-unified`, `nextjs-unified` и другие |

### Создание собственной конфигурации

```bash
# Вариант 1: Интерактивный
skill-seekers scrape --interactive

# Вариант 2: Копирование и редактирование пресета
cp configs/react.json configs/myframework.json
nano configs/myframework.json
skill-seekers scrape --config configs/myframework.json
```

### Структура файла конфигурации

```json
{
  "name": "myframework",
  "description": "Когда использовать этот навык",
  "base_url": "https://docs.myframework.com/",
  "selectors": {
    "main_content": "article",
    "title": "h1",
    "code_blocks": "pre code"
  },
  "url_patterns": {
    "include": ["/docs", "/guide"],
    "exclude": ["/blog", "/about"]
  },
  "categories": {
    "getting_started": ["intro", "quickstart"],
    "api": ["api", "reference"]
  },
  "rate_limit": 0.5,
  "max_pages": 500
}
```

### Где хранить конфигурации

Инструмент выполняет поиск в следующем порядке:
1. Точный путь, как указан
2. `./configs/` (текущая директория)
3. `~/.config/skill-seekers/configs/` (пользовательская директория конфигурации)
4. SkillSeekersWeb.com API (готовые конфигурации)

---

## 📊 Что создаётся

```
output/
├── godot_data/              # Полученные необработанные данные
│   ├── pages/              # JSON-файлы (по одному на страницу)
│   └── summary.json        # Обзор
│
└── godot/                   # Навык
    ├── SKILL.md            # Улучшенный с реальными примерами
    ├── references/         # Категоризированная документация
    │   ├── index.md
    │   ├── getting_started.md
    │   ├── scripting.md
    │   └── ...
    ├── scripts/            # Пусто (добавьте свои скрипты)
    └── assets/             # Пусто (добавьте свои ресурсы)
```

---

## 🐛 Устранение неполадок

### Контент не извлечён?
- Проверьте селектор `main_content`
- Попробуйте: `article`, `main`, `div[role="main"]`

### Данные есть, но не используются?
```bash
# Принудительное повторное сканирование
rm -rf output/myframework_data/
skill-seekers scrape --config configs/myframework.json
```

### Категоризация не устраивает?
Отредактируйте раздел `categories` в конфигурации, используя более подходящие ключевые слова.

### Хотите обновить документацию?
```bash
# Удалите старые данные и просканируйте заново
rm -rf output/godot_data/
skill-seekers scrape --config configs/godot.json
```

### Улучшение не работает?
```bash
# Проверьте, установлен ли API Key
echo $ANTHROPIC_API_KEY

# Попробуйте LOCAL-режим (использует Claude Code Max, API Key не нужен)
skill-seekers enhance output/react/ --mode LOCAL

# Мониторинг статуса фонового улучшения
skill-seekers enhance-status output/react/ --watch
```

### Проблемы с лимитами GitHub?
```bash
# Установите GitHub Token (5000 запросов/час вместо 60/час анонимно)
export GITHUB_TOKEN=ghp_your_token_here

# Или настройте несколько профилей
skill-seekers config --github
```

---

## 📈 Производительность

| Задача | Время | Примечания |
|--------|-------|-----------|
| Сканирование (синхр.) | 15–45 мин | Только первый раз, на основе потоков |
| Сканирование (асинхр.) | 5–15 мин | В 2–3 раза быстрее с флагом `--async` |
| Сборка | 1–3 мин | Быстрая пересборка из кэша |
| Пересборка | <1 мин | С `--skip-scrape` |
| Улучшение (LOCAL) | 30–60 сек | Использует Claude Code Max |
| Улучшение (API) | 20–40 сек | Требуется API Key |
| Видео (субтитры) | 1–3 мин | YouTube/локальное, только субтитры |
| Видео (визуальное) | 5–15 мин | + OCR-извлечение кадров |
| Упаковка | 5–10 сек | Создание итогового .zip |

---

## 📚 Документация

### Начало работы
- **[BULLETPROOF_QUICKSTART.md](BULLETPROOF_QUICKSTART.md)** — 🎯 **НАЧНИТЕ ЗДЕСЬ**, если вы новичок!
- **[QUICKSTART.md](QUICKSTART.md)** — Быстрый старт для опытных пользователей
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** — Распространённые проблемы и решения
- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** — Краткая справка на одну страницу

### Руководства
- **[docs/LARGE_DOCUMENTATION.md](docs/LARGE_DOCUMENTATION.md)** — Работа с документами на 10K–40K+ страниц
- **[ASYNC_SUPPORT.md](ASYNC_SUPPORT.md)** — Руководство по асинхронному режиму (в 2–3 раза быстрее)
- **[docs/ENHANCEMENT_MODES.md](docs/ENHANCEMENT_MODES.md)** — Руководство по режимам ИИ-улучшения
- **[docs/MCP_SETUP.md](docs/MCP_SETUP.md)** — Настройка MCP-интеграции
- **[docs/UNIFIED_SCRAPING.md](docs/UNIFIED_SCRAPING.md)** — Мультиисточниковое сканирование
- **[docs/VIDEO_GUIDE.md](docs/VIDEO_GUIDE.md)** — Полное руководство по извлечению из видео

### Руководства по интеграции
- **[docs/integrations/LANGCHAIN.md](docs/integrations/LANGCHAIN.md)** — LangChain RAG
- **[docs/integrations/CURSOR.md](docs/integrations/CURSOR.md)** — Cursor IDE
- **[docs/integrations/WINDSURF.md](docs/integrations/WINDSURF.md)** — Windsurf IDE
- **[docs/integrations/CLINE.md](docs/integrations/CLINE.md)** — Cline (VS Code)
- **[docs/integrations/RAG_PIPELINES.md](docs/integrations/RAG_PIPELINES.md)** — Все RAG-конвейеры

---

## 📝 Лицензия

Лицензия MIT — подробности в файле [LICENSE](LICENSE)

---

Удачного создания навыков! 🚀

---

## 🔒 Безопасность

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/yusufkaraaslan-skill-seekers-badge.png)](https://mseep.ai/app/yusufkaraaslan-skill-seekers)
