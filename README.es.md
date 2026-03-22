<p align="center">
  <img src="docs/assets/logo.png" alt="Skill Seekers" width="200"/>
</p>

# Skill Seekers

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | Español | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md) | [Türkçe](README.tr.md) | [العربية](README.ar.md) | [हिन्दी](README.hi.md) | [Русский](README.ru.md)

> ⚠️ **Aviso de traducción automática**
>
> Este documento ha sido traducido automáticamente por IA. Aunque nos esforzamos por garantizar la calidad, pueden existir expresiones inexactas.
>
> ¡Ayúdanos a mejorar la traducción a través de [GitHub Issue #260](https://github.com/yusufkaraaslan/Skill_Seekers/issues/260)! Tu retroalimentación es muy valiosa para nosotros.

[![Versión](https://img.shields.io/badge/version-3.2.0-blue.svg)](https://github.com/yusufkaraaslan/Skill_Seekers/releases)
[![Licencia: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Integración MCP](https://img.shields.io/badge/MCP-Integrated-blue.svg)](https://modelcontextprotocol.io)
[![Tests aprobados](https://img.shields.io/badge/Tests-2540%2B%20Passing-brightgreen.svg)](tests/)
[![Tablero del proyecto](https://img.shields.io/badge/Project-Board-purple.svg)](https://github.com/users/yusufkaraaslan/projects/2)
[![Versión PyPI](https://badge.fury.io/py/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![PyPI - Descargas](https://img.shields.io/pypi/dm/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![PyPI - Versión de Python](https://img.shields.io/pypi/pyversions/skill-seekers.svg)](https://pypi.org/project/skill-seekers/)
[![Sitio web](https://img.shields.io/badge/Website-skillseekersweb.com-blue.svg)](https://skillseekersweb.com/)
[![Seguir en Twitter](https://img.shields.io/twitter/follow/_yUSyUS_?style=social)](https://x.com/_yUSyUS_)
[![Estrellas en GitHub](https://img.shields.io/github/stars/yusufkaraaslan/Skill_Seekers?style=social)](https://github.com/yusufkaraaslan/Skill_Seekers)

**🧠 La capa de datos para sistemas de IA.** Skill Seekers convierte sitios de documentación, repositorios de GitHub, PDFs, videos, notebooks, wikis y más de 10 tipos de fuentes adicionales en activos de conocimiento estructurado, listos para potenciar AI Skills (Claude, Gemini, OpenAI), pipelines RAG (LangChain, LlamaIndex, Pinecone) y asistentes de programación con IA (Cursor, Windsurf, Cline) en minutos, no en horas.

> 🌐 **[Visita SkillSeekersWeb.com](https://skillseekersweb.com/)** - ¡Explora más de 24 configuraciones predefinidas, comparte tus configuraciones y accede a la documentación completa!

> 📋 **[Ver hoja de ruta y tareas de desarrollo](https://github.com/users/yusufkaraaslan/projects/2)** - ¡134 tareas en 10 categorías, elige cualquiera para contribuir!

## 🌐 Ecosistema

Skill Seekers es un proyecto multi-repositorio. Aquí es donde vive todo:

| Repositorio | Descripción | Enlaces |
|------------|-------------|---------|
| **[Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers)** | CLI principal y servidor MCP (este repo) | [PyPI](https://pypi.org/project/skill-seekers/) |
| **[skillseekersweb](https://github.com/yusufkaraaslan/skillseekersweb)** | Sitio web y documentación | [Web](https://skillseekersweb.com/) |
| **[skill-seekers-configs](https://github.com/yusufkaraaslan/skill-seekers-configs)** | Repositorio de configuraciones comunitarias | |
| **[skill-seekers-action](https://github.com/yusufkaraaslan/skill-seekers-action)** | GitHub Action para CI/CD | |
| **[skill-seekers-plugin](https://github.com/yusufkaraaslan/skill-seekers-plugin)** | Plugin para Claude Code | |
| **[homebrew-skill-seekers](https://github.com/yusufkaraaslan/homebrew-skill-seekers)** | Homebrew tap para macOS | |

> **¿Quieres contribuir?** ¡Los repos del sitio web y configuraciones son excelentes puntos de partida para nuevos colaboradores!

## 🧠 La capa de datos para sistemas de IA

**Skill Seekers es la capa universal de preprocesamiento** que se ubica entre la documentación sin procesar y cada sistema de IA que la consume. Ya sea que estés construyendo Claude Skills, un pipeline RAG con LangChain o un archivo `.cursorrules` para Cursor, la preparación de datos es idéntica. Lo haces una vez y exportas a todos los destinos.

```bash
# Un comando → activo de conocimiento estructurado
skill-seekers create https://docs.react.dev/
# o: skill-seekers create facebook/react
# o: skill-seekers create ./my-project

# Exportar a cualquier sistema de IA
skill-seekers package output/react --target claude      # → Claude AI Skill (ZIP)
skill-seekers package output/react --target langchain   # → LangChain Documents
skill-seekers package output/react --target llama-index # → LlamaIndex TextNodes
skill-seekers package output/react --target cursor      # → .cursorrules
```

### Lo que se genera

| Salida | Destino | Para qué sirve |
|--------|---------|-----------------|
| **Claude Skill** (ZIP + YAML) | `--target claude` | Claude Code, Claude API |
| **Gemini Skill** (tar.gz) | `--target gemini` | Google Gemini |
| **OpenAI / Custom GPT** (ZIP) | `--target openai` | GPT-4o, asistentes personalizados |
| **LangChain Documents** | `--target langchain` | Cadenas QA, agentes, recuperadores |
| **LlamaIndex TextNodes** | `--target llama-index` | Motores de consulta, motores de chat |
| **Haystack Documents** | `--target haystack` | Pipelines RAG empresariales |
| **Pinecone-ready** (Markdown) | `--target markdown` | Carga de vectores |
| **ChromaDB / FAISS / Qdrant** | `--format chroma/faiss/qdrant` | Bases de datos vectoriales locales |
| **Cursor** `.cursorrules` | `--target claude` → copiar | Contexto IA del IDE Cursor |
| **Windsurf / Cline / Continue** | `--target claude` → copiar | VS Code, IntelliJ, Vim |

### Por qué es importante

- ⚡ **99% más rápido** — Días de preparación manual → 15–45 minutos
- 🎯 **Calidad de AI Skill** — Archivos SKILL.md de más de 500 líneas con ejemplos, patrones y guías
- 📊 **Fragmentos listos para RAG** — Fragmentación inteligente que preserva bloques de código y mantiene el contexto
- 🎬 **Videos** — Extrae código, transcripciones y conocimiento estructurado de YouTube y videos locales
- 🔄 **Multi-fuente** — Combina 17 tipos de fuentes (docs, GitHub, PDFs, videos, notebooks, wikis y más) en un solo activo de conocimiento
- 🌐 **Una preparación, todos los destinos** — Exporta el mismo activo a 16 plataformas sin volver a extraer
- ✅ **Probado en producción** — Más de 2.540 tests, más de 24 presets de frameworks, listo para producción

## 🚀 Inicio rápido (3 comandos)

```bash
# 1. Instalar
pip install skill-seekers

# 2. Crear skill desde cualquier fuente
skill-seekers create https://docs.django.com/

# 3. Empaquetar para tu plataforma de IA
skill-seekers package output/django --target claude
```

**¡Eso es todo!** Ahora tienes `output/django-claude.zip` listo para usar.

### Otras fuentes (17 soportadas)

```bash
# Repositorio de GitHub
skill-seekers create facebook/react

# Proyecto local
skill-seekers create ./my-project

# Documento PDF
skill-seekers create manual.pdf

# Documento Word
skill-seekers create report.docx

# Libro electrónico EPUB
skill-seekers create book.epub

# Jupyter Notebook
skill-seekers create notebook.ipynb

# Especificación OpenAPI
skill-seekers create openapi.yaml

# Presentación PowerPoint
skill-seekers create presentation.pptx

# Documento AsciiDoc
skill-seekers create guide.adoc

# Archivo HTML local
skill-seekers create page.html

# Feed RSS/Atom
skill-seekers create feed.rss

# Página de manual
skill-seekers create curl.1

# Video (YouTube, Vimeo o archivo local — requiere skill-seekers[video])
skill-seekers video --url https://www.youtube.com/watch?v=... --name mytutorial
# ¿Primera vez? Instala automáticamente las dependencias visuales con detección de GPU:
skill-seekers video --setup

# Wiki de Confluence
skill-seekers confluence --space TEAM --name wiki

# Páginas de Notion
skill-seekers notion --database-id ... --name docs

# Exportación de chat de Slack/Discord
skill-seekers chat --export-dir ./slack-export --name team-chat
```

### Exportar a todas partes

```bash
# Empaquetar para múltiples plataformas
for platform in claude gemini openai langchain; do
  skill-seekers package output/django --target $platform
done
```

## ¿Qué es Skill Seekers?

Skill Seekers es la **capa de datos para sistemas de IA**. Transforma 17 tipos de fuentes —sitios web de documentación, repositorios de GitHub, PDFs, videos, Jupyter Notebooks, documentos Word/EPUB/AsciiDoc, especificaciones OpenAPI, presentaciones PowerPoint, feeds RSS, páginas de manual, wikis de Confluence, páginas de Notion, exportaciones de Slack/Discord y más— en activos de conocimiento estructurado para cualquier destino de IA:

| Caso de uso | Lo que obtienes | Ejemplos |
|-------------|-----------------|----------|
| **AI Skills** | SKILL.md completo + referencias | Claude Code, Gemini, GPT |
| **Pipelines RAG** | Documentos fragmentados con metadatos enriquecidos | LangChain, LlamaIndex, Haystack |
| **Bases de datos vectoriales** | Datos pre-formateados listos para carga | Pinecone, Chroma, Weaviate, FAISS |
| **Asistentes de programación con IA** | Archivos de contexto que tu IDE IA lee automáticamente | Cursor, Windsurf, Cline, Continue.dev |

En lugar de pasar días en preprocesamiento manual, Skill Seekers:

1. **Ingesta** — documentación, repositorios de GitHub, bases de código locales, PDFs, videos, notebooks, wikis y más de 10 tipos de fuentes adicionales
2. **Analiza** — análisis profundo AST, detección de patrones, extracción de APIs
3. **Estructura** — archivos de referencia categorizados con metadatos
4. **Mejora** — generación de SKILL.md potenciada por IA (Claude, Gemini o local)
5. **Exporta** — 16 formatos específicos por plataforma desde un solo activo

## ¿Por qué usar Skill Seekers?

### Para constructores de AI Skills (Claude, Gemini, OpenAI)

- 🎯 **Skills de nivel producción** — Archivos SKILL.md de más de 500 líneas con ejemplos de código, patrones y guías
- 🔄 **Flujos de mejora** — Aplica presets como `security-focus`, `architecture-comprehensive` o YAML personalizados
- 🎮 **Cualquier dominio** — Motores de juegos (Godot, Unity), frameworks (React, Django), herramientas internas
- 🔧 **Equipos** — Combina documentación interna + código en una única fuente de verdad
- 📚 **Calidad** — Mejorado con IA, incluye ejemplos, referencia rápida y guía de navegación

### Para constructores de RAG e ingenieros de IA

- 🤖 **Datos listos para RAG** — `Documents` de LangChain, `TextNodes` de LlamaIndex y `Documents` de Haystack pre-fragmentados
- 🚀 **99% más rápido** — Días de preprocesamiento → 15–45 minutos
- 📊 **Metadatos inteligentes** — Categorías, fuentes, tipos → mayor precisión en la recuperación
- 🔄 **Multi-fuente** — Combina docs + GitHub + PDFs + videos en un solo pipeline
- 🌐 **Agnóstico de plataforma** — Exporta a cualquier base de datos vectorial o framework sin volver a extraer

### Para usuarios de asistentes de programación con IA

- 💻 **Cursor / Windsurf / Cline** — Genera `.cursorrules` / `.windsurfrules` / `.clinerules` automáticamente
- 🎯 **Contexto persistente** — La IA "conoce" tus frameworks sin necesidad de repetir prompts
- 📚 **Siempre actualizado** — Actualiza el contexto en minutos cuando cambia la documentación

## Funcionalidades clave

### 🌐 Extracción de documentación
- ✅ **Soporte para llms.txt** - Detecta y usa automáticamente archivos de documentación optimizados para LLM (10 veces más rápido)
- ✅ **Scraper universal** - Funciona con CUALQUIER sitio web de documentación
- ✅ **Categorización inteligente** - Organiza automáticamente el contenido por tema
- ✅ **Detección de lenguajes de código** - Reconoce Python, JavaScript, C++, GDScript, etc.
- ✅ **Más de 24 presets listos para usar** - Godot, React, Vue, Django, FastAPI y más

### 📄 Soporte para PDF
- ✅ **Extracción básica de PDF** - Extrae texto, código e imágenes de archivos PDF
- ✅ **OCR para PDFs escaneados** - Extrae texto de documentos escaneados
- ✅ **PDFs protegidos con contraseña** - Maneja PDFs cifrados
- ✅ **Extracción de tablas** - Extrae tablas complejas de PDFs
- ✅ **Procesamiento en paralelo** - 3 veces más rápido para PDFs grandes
- ✅ **Caché inteligente** - 50% más rápido en ejecuciones posteriores

### 🎬 Extracción de video
- ✅ **YouTube y videos locales** - Extrae transcripciones, código en pantalla y conocimiento estructurado de videos
- ✅ **Análisis visual de fotogramas** - Extracción OCR de editores de código, terminales, diapositivas y diagramas
- ✅ **Detección automática de GPU** - Instala automáticamente la compilación correcta de PyTorch (CUDA/ROCm/MPS/CPU)
- ✅ **Mejora con IA** - Dos pasadas: limpieza de artefactos OCR + generación de SKILL.md pulido
- ✅ **Recorte temporal** - Extrae secciones específicas con `--start-time` y `--end-time`
- ✅ **Soporte para listas de reproducción** - Procesa por lotes todos los videos de una lista de reproducción de YouTube
- ✅ **Respaldo con Vision API** - Usa Claude Vision para fotogramas OCR de baja confianza

### 🐙 Análisis de repositorios de GitHub
- ✅ **Análisis profundo de código** - Análisis AST para Python, JavaScript, TypeScript, Java, C++, Go
- ✅ **Extracción de APIs** - Funciones, clases, métodos con parámetros y tipos
- ✅ **Metadatos del repositorio** - README, árbol de archivos, desglose de lenguajes, estrellas/forks
- ✅ **GitHub Issues y PRs** - Obtiene issues abiertos/cerrados con etiquetas e hitos
- ✅ **CHANGELOG y releases** - Extrae automáticamente el historial de versiones
- ✅ **Detección de conflictos** - Compara APIs documentadas vs. implementación real del código
- ✅ **Integración MCP** - Lenguaje natural: "Extrae el repositorio de GitHub facebook/react"

### 🔄 Extracción unificada multi-fuente
- ✅ **Combina múltiples fuentes** - Mezcla documentación + GitHub + PDF en un solo skill
- ✅ **Detección de conflictos** - Encuentra automáticamente discrepancias entre docs y código
- ✅ **Fusión inteligente** - Resolución de conflictos basada en reglas o potenciada por IA
- ✅ **Informes transparentes** - Comparación lado a lado con advertencias ⚠️
- ✅ **Análisis de brechas en documentación** - Identifica docs obsoletos y funcionalidades no documentadas
- ✅ **Fuente única de verdad** - Un solo skill que muestra tanto la intención (docs) como la realidad (código)
- ✅ **Compatible con versiones anteriores** - Las configuraciones de fuente única legacy siguen funcionando

### 🤖 Soporte para múltiples plataformas LLM
- ✅ **12 plataformas LLM** - Claude AI, Google Gemini, OpenAI ChatGPT, MiniMax AI, Markdown genérico, OpenCode, Kimi, DeepSeek, Qwen, OpenRouter, Together AI, Fireworks AI
- ✅ **Extracción universal** - La misma documentación funciona para todas las plataformas
- ✅ **Empaquetado específico por plataforma** - Formatos optimizados para cada LLM
- ✅ **Exportación con un solo comando** - El flag `--target` selecciona la plataforma
- ✅ **Dependencias opcionales** - Instala solo lo que necesitas
- ✅ **100% compatible con versiones anteriores** - Los flujos de trabajo existentes de Claude no cambian

| Plataforma | Formato | Carga | Mejora | API Key | Endpoint personalizado |
|------------|---------|-------|--------|---------|------------------------|
| **Claude AI** | ZIP + YAML | ✅ Automática | ✅ Sí | ANTHROPIC_API_KEY | ANTHROPIC_BASE_URL |
| **Google Gemini** | tar.gz | ✅ Automática | ✅ Sí | GOOGLE_API_KEY | - |
| **OpenAI ChatGPT** | ZIP + Vector Store | ✅ Automática | ✅ Sí | OPENAI_API_KEY | - |
| **Markdown genérico** | ZIP | ❌ Manual | ❌ No | - | - |

```bash
# Claude (predeterminado - ¡sin cambios necesarios!)
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

# Markdown genérico (exportación universal)
skill-seekers package output/react/ --target markdown
# Usa los archivos markdown directamente en cualquier LLM
```

<details>
<summary>🔧 <strong>Variables de entorno para APIs compatibles con Claude (ej. GLM-4.7)</strong></summary>

Skill Seekers soporta cualquier endpoint de API compatible con Claude:

```bash
# Opción 1: API oficial de Anthropic (predeterminado)
export ANTHROPIC_API_KEY=sk-ant-...

# Opción 2: API compatible con Claude de GLM-4.7
export ANTHROPIC_API_KEY=your-glm-47-api-key
export ANTHROPIC_BASE_URL=https://glm-4-7-endpoint.com/v1

# Todas las funciones de mejora con IA usarán el endpoint configurado
skill-seekers enhance output/react/
skill-seekers analyze --directory . --enhance
```

**Nota**: Configurar `ANTHROPIC_BASE_URL` permite usar cualquier endpoint de API compatible con Claude, como GLM-4.7 (智谱 AI) u otros servicios compatibles.

</details>

**Instalación:**
```bash
# Instalar con soporte para Gemini
pip install skill-seekers[gemini]

# Instalar con soporte para OpenAI
pip install skill-seekers[openai]

# Instalar con todas las plataformas LLM
pip install skill-seekers[all-llms]
```

### 🔗 Integraciones con frameworks RAG

- ✅ **LangChain Documents** - Exportación directa al formato `Document` con `page_content` + metadatos
  - Ideal para: cadenas QA, recuperadores, almacenes de vectores, agentes
  - Ejemplo: [Pipeline RAG con LangChain](examples/langchain-rag-pipeline/)
  - Guía: [Integración con LangChain](docs/integrations/LANGCHAIN.md)

- ✅ **LlamaIndex TextNodes** - Exportación al formato `TextNode` con IDs únicos + embeddings
  - Ideal para: motores de consulta, motores de chat, contexto de almacenamiento
  - Ejemplo: [Motor de consulta LlamaIndex](examples/llama-index-query-engine/)
  - Guía: [Integración con LlamaIndex](docs/integrations/LLAMA_INDEX.md)

- ✅ **Formato listo para Pinecone** - Optimizado para carga en bases de datos vectoriales
  - Ideal para: búsqueda vectorial en producción, búsqueda semántica, búsqueda híbrida
  - Ejemplo: [Carga en Pinecone](examples/pinecone-upsert/)
  - Guía: [Integración con Pinecone](docs/integrations/PINECONE.md)

**Exportación rápida:**
```bash
# LangChain Documents (JSON)
skill-seekers package output/django --target langchain
# → output/django-langchain.json

# LlamaIndex TextNodes (JSON)
skill-seekers package output/django --target llama-index
# → output/django-llama-index.json

# Markdown (universal)
skill-seekers package output/django --target markdown
# → output/django-markdown/SKILL.md + references/
```

**Guía completa de pipelines RAG:** [Documentación de pipelines RAG](docs/integrations/RAG_PIPELINES.md)

---

### 🧠 Integraciones con asistentes de programación con IA

Transforma cualquier documentación de framework en contexto experto de programación para más de 4 asistentes de IA:

- ✅ **Cursor IDE** - Genera `.cursorrules` para sugerencias de código potenciadas por IA
  - Ideal para: generación de código específica por framework, patrones consistentes
  - Funciona con: Cursor IDE (fork de VS Code)
  - Guía: [Integración con Cursor](docs/integrations/CURSOR.md)
  - Ejemplo: [Skill de React para Cursor](examples/cursor-react-skill/)

- ✅ **Windsurf** - Personaliza el contexto del asistente IA de Windsurf con `.windsurfrules`
  - Ideal para: asistencia IA nativa del IDE, programación basada en flujos
  - Funciona con: Windsurf IDE de Codeium
  - Guía: [Integración con Windsurf](docs/integrations/WINDSURF.md)
  - Ejemplo: [Contexto FastAPI para Windsurf](examples/windsurf-fastapi-context/)

- ✅ **Cline (VS Code)** - Prompts de sistema + MCP para el agente de VS Code
  - Ideal para: generación de código agéntica en VS Code
  - Funciona con: extensión Cline para VS Code
  - Guía: [Integración con Cline](docs/integrations/CLINE.md)
  - Ejemplo: [Asistente Django para Cline](examples/cline-django-assistant/)

- ✅ **Continue.dev** - Servidores de contexto para IA independiente del IDE
  - Ideal para: entornos multi-IDE (VS Code, JetBrains, Vim), proveedores LLM personalizados
  - Funciona con: cualquier IDE con el plugin Continue.dev
  - Guía: [Integración con Continue](docs/integrations/CONTINUE_DEV.md)
  - Ejemplo: [Contexto universal de Continue](examples/continue-dev-universal/)

**Exportación rápida para herramientas de programación con IA:**
```bash
# Para cualquier asistente de programación con IA (Cursor, Windsurf, Cline, Continue.dev)
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target claude  # o --target markdown

# Copiar a tu proyecto (ejemplo para Cursor)
cp output/django-claude/SKILL.md my-project/.cursorrules

# O para Windsurf
cp output/django-claude/SKILL.md my-project/.windsurf/rules/django.md

# O para Cline
cp output/django-claude/SKILL.md my-project/.clinerules

# O para Continue.dev (servidor HTTP)
python examples/continue-dev-universal/context_server.py
# Configurar en ~/.continue/config.json
```

**Centro de integraciones:** [Todas las integraciones con sistemas de IA](docs/integrations/INTEGRATIONS.md)

---

### 🌊 Arquitectura de tres flujos para GitHub
- ✅ **Análisis de triple flujo** - Divide los repos de GitHub en flujos de Código, Documentación e Insights
- ✅ **Analizador de código unificado** - Funciona con URLs de GitHub Y rutas locales
- ✅ **C3.x como profundidad de análisis** - Elige entre 'basic' (1–2 min) o 'c3x' (20–60 min)
- ✅ **Generación mejorada del router** - Metadatos de GitHub, inicio rápido del README, problemas comunes
- ✅ **Integración de issues** - Problemas principales y soluciones desde GitHub Issues
- ✅ **Palabras clave de enrutamiento inteligente** - Etiquetas de GitHub con peso 2x para mejor detección de temas

**Los tres flujos explicados:**
- **Flujo 1: Código** - Análisis profundo C3.x (patrones, ejemplos, guías, configuraciones, arquitectura)
- **Flujo 2: Documentación** - Documentación del repositorio (README, CONTRIBUTING, docs/*.md)
- **Flujo 3: Insights** - Conocimiento de la comunidad (issues, etiquetas, estrellas, forks)

```python
from skill_seekers.cli.unified_codebase_analyzer import UnifiedCodebaseAnalyzer

# Analizar repositorio de GitHub con los tres flujos
analyzer = UnifiedCodebaseAnalyzer()
result = analyzer.analyze(
    source="https://github.com/facebook/react",
    depth="c3x",  # o "basic" para análisis rápido
    fetch_github_metadata=True
)

# Acceder al flujo de código (análisis C3.x)
print(f"Patrones de diseño: {len(result.code_analysis['c3_1_patterns'])}")
print(f"Ejemplos de tests: {result.code_analysis['c3_2_examples_count']}")

# Acceder al flujo de documentación (docs del repositorio)
print(f"README: {result.github_docs['readme'][:100]}")

# Acceder al flujo de insights (metadatos de GitHub)
print(f"Estrellas: {result.github_insights['metadata']['stars']}")
print(f"Problemas comunes: {len(result.github_insights['common_problems'])}")
```

**Documentación completa**: [Resumen de implementación de tres flujos](docs/IMPLEMENTATION_SUMMARY_THREE_STREAM.md)

### 🔐 Gestión inteligente de límites de tasa y configuración
- ✅ **Sistema de configuración multi-token** - Gestiona múltiples cuentas de GitHub (personal, trabajo, OSS)
  - Almacenamiento seguro de configuración en `~/.config/skill-seekers/config.json` (permisos 600)
  - Estrategias de límite de tasa por perfil: `prompt`, `wait`, `switch`, `fail`
  - Timeout configurable por perfil (predeterminado: 30 min, evita esperas indefinidas)
  - Cadena inteligente de respaldo: argumento CLI → variable de entorno → archivo de configuración → prompt
  - Gestión de API keys para Claude, Gemini, OpenAI
- ✅ **Asistente de configuración interactivo** - Interfaz de terminal atractiva para fácil configuración
  - Integración con navegador para creación de tokens (abre automáticamente GitHub, etc.)
  - Validación de tokens y pruebas de conexión
  - Visualización de estado con códigos de color
- ✅ **Manejador inteligente de límites de tasa** - ¡No más esperas indefinidas!
  - Advertencia anticipada sobre límites de tasa (60/hora vs 5000/hora)
  - Detección en tiempo real desde las respuestas de la API de GitHub
  - Temporizadores de cuenta regresiva en vivo con progreso
  - Cambio automático de perfil cuando se alcanza el límite
  - Cuatro estrategias: prompt (preguntar), wait (cuenta regresiva), switch (cambiar a otro), fail (abortar)
- ✅ **Capacidad de reanudación** - Continúa trabajos interrumpidos
  - Auto-guardado de progreso en intervalos configurables (predeterminado: 60 seg)
  - Lista todos los trabajos reanudables con detalles de progreso
  - Limpieza automática de trabajos antiguos (predeterminado: 7 días)
- ✅ **Soporte CI/CD** - Modo no interactivo para automatización
  - Flag `--non-interactive` que falla rápidamente sin prompts
  - Flag `--profile` para seleccionar una cuenta de GitHub específica
  - Mensajes de error claros para logs de pipelines

**Configuración rápida:**
```bash
# Configuración única (5 minutos)
skill-seekers config --github

# Usar perfil específico para repos privados
skill-seekers github --repo mycompany/private-repo --profile work

# Modo CI/CD (fallo rápido, sin prompts)
skill-seekers github --repo owner/repo --non-interactive

# Reanudar trabajo interrumpido
skill-seekers resume --list
skill-seekers resume github_react_20260117_143022
```

**Estrategias de límite de tasa explicadas:**
- **prompt** (predeterminado) - Pregunta qué hacer cuando se alcanza el límite (esperar, cambiar, configurar token, cancelar)
- **wait** - Espera automáticamente con temporizador de cuenta regresiva (respeta el timeout)
- **switch** - Intenta automáticamente el siguiente perfil disponible (para configuraciones multi-cuenta)
- **fail** - Falla inmediatamente con error claro (perfecto para CI/CD)

### 🎯 Skill Bootstrap - Auto-alojamiento

Genera skill-seekers como un Claude Code Skill para usarlo dentro de Claude:

```bash
# Generar el skill
./scripts/bootstrap_skill.sh

# Instalar en Claude Code
cp -r output/skill-seekers ~/.claude/skills/
```

**Lo que obtienes:**
- ✅ **Documentación completa del skill** - Todos los comandos CLI y patrones de uso
- ✅ **Referencia de comandos CLI** - Cada herramienta y sus opciones documentadas
- ✅ **Ejemplos de inicio rápido** - Flujos de trabajo comunes y mejores prácticas
- ✅ **Documentación de API auto-generada** - Análisis de código, patrones y ejemplos

### 🔐 Repositorios de configuración privados
- ✅ **Fuentes de configuración basadas en Git** - Obtén configuraciones desde repositorios git privados/de equipo
- ✅ **Gestión multi-fuente** - Registra repositorios ilimitados de GitHub, GitLab, Bitbucket
- ✅ **Colaboración en equipo** - Comparte configuraciones personalizadas entre equipos de 3–5 personas
- ✅ **Soporte empresarial** - Escala a más de 500 desarrolladores con resolución basada en prioridad
- ✅ **Autenticación segura** - Tokens como variables de entorno (GITHUB_TOKEN, GITLAB_TOKEN)
- ✅ **Caché inteligente** - Clona una vez, obtiene actualizaciones automáticamente
- ✅ **Modo offline** - Trabaja con configuraciones en caché cuando no hay conexión

### 🤖 Análisis de código (C3.x)

**C3.4: Extracción de patrones de configuración con mejora por IA**
- ✅ **9 formatos de configuración** - JSON, YAML, TOML, ENV, INI, Python, JavaScript, Dockerfile, Docker Compose
- ✅ **7 tipos de patrones** - Configuraciones de base de datos, API, logging, caché, correo, autenticación, servidor
- ✅ **Mejora con IA** - Análisis IA opcional en modo dual (API + LOCAL)
  - Explica qué hace cada configuración
  - Sugiere mejores prácticas y mejoras
  - **Análisis de seguridad** - Encuentra secretos codificados y credenciales expuestas
- ✅ **Auto-documentación** - Genera documentación JSON + Markdown de todas las configuraciones
- ✅ **Integración MCP** - Herramienta `extract_config_patterns` con soporte de mejora

**C3.3: Guías prácticas mejoradas con IA**
- ✅ **Mejora integral con IA** - Transforma guías básicas en tutoriales profesionales
- ✅ **5 mejoras automáticas** - Descripciones de pasos, solución de problemas, prerrequisitos, siguientes pasos, casos de uso
- ✅ **Soporte de modo dual** - Modo API (Claude API) o modo LOCAL (Claude Code CLI)
- ✅ **Sin costos con modo LOCAL** - Mejora GRATUITA usando tu plan Claude Code Max
- ✅ **Transformación de calidad** - Plantillas de 75 líneas → guías completas de más de 500 líneas

**Uso:**
```bash
# Análisis rápido (1–2 min, solo funciones básicas)
skill-seekers analyze --directory tests/ --quick

# Análisis completo con IA (20–60 min, todas las funciones)
skill-seekers analyze --directory tests/ --comprehensive

# Con mejora por IA
skill-seekers analyze --directory tests/ --enhance
```

**Documentación completa:** [docs/HOW_TO_GUIDES.md](docs/HOW_TO_GUIDES.md#ai-enhancement-new)

### 🔄 Presets de flujo de trabajo de mejora

Pipelines de mejora reutilizables definidos en YAML que controlan cómo la IA transforma tu documentación sin procesar en un skill pulido.

- ✅ **5 presets incluidos** — `default`, `minimal`, `security-focus`, `architecture-comprehensive`, `api-documentation`
- ✅ **Presets definidos por el usuario** — añade flujos personalizados a `~/.config/skill-seekers/workflows/`
- ✅ **Múltiples flujos de trabajo** — encadena dos o más flujos en un solo comando
- ✅ **CLI completamente gestionado** — lista, inspecciona, copia, añade, elimina y valida flujos de trabajo

```bash
# Aplicar un solo flujo de trabajo
skill-seekers create ./my-project --enhance-workflow security-focus

# Encadenar múltiples flujos de trabajo (se aplican en orden)
skill-seekers create ./my-project \
  --enhance-workflow security-focus \
  --enhance-workflow minimal

# Gestionar presets
skill-seekers workflows list                          # Listar todos (incluidos + usuario)
skill-seekers workflows show security-focus           # Mostrar contenido YAML
skill-seekers workflows copy security-focus           # Copiar al directorio de usuario para editar
skill-seekers workflows add ./my-workflow.yaml        # Instalar un preset personalizado
skill-seekers workflows remove my-workflow            # Eliminar un preset de usuario
skill-seekers workflows validate security-focus       # Validar estructura del preset

# Copiar varios a la vez
skill-seekers workflows copy security-focus minimal api-documentation

# Añadir varios archivos a la vez
skill-seekers workflows add ./wf-a.yaml ./wf-b.yaml

# Eliminar varios a la vez
skill-seekers workflows remove my-wf-a my-wf-b
```

**Formato de preset YAML:**
```yaml
name: security-focus
description: "Revisión enfocada en seguridad: vulnerabilidades, autenticación, manejo de datos"
version: "1.0"
stages:
  - name: vulnerabilities
    type: custom
    prompt: "Revisar el OWASP top 10 y vulnerabilidades de seguridad comunes..."
  - name: auth-review
    type: custom
    prompt: "Examinar patrones de autenticación y autorización..."
    uses_history: true
```

### ⚡ Rendimiento y escalabilidad
- ✅ **Modo asíncrono** - Extracción 2–3x más rápida con async/await (usa el flag `--async`)
- ✅ **Soporte para documentación grande** - Maneja documentos de 10K–40K+ páginas con división inteligente
- ✅ **Skills Router/Hub** - Enrutamiento inteligente hacia sub-skills especializados
- ✅ **Extracción en paralelo** - Procesa múltiples skills simultáneamente
- ✅ **Checkpoint/Reanudación** - Nunca pierdas progreso en extracciones largas
- ✅ **Sistema de caché** - Extrae una vez, reconstruye instantáneamente

### ✅ Garantía de calidad
- ✅ **Completamente probado** - Más de 2.540 tests con cobertura completa

---

## 📦 Instalación

```bash
# Instalación básica (extracción de documentación, análisis de GitHub, PDF, empaquetado)
pip install skill-seekers

# Con soporte para todas las plataformas LLM
pip install skill-seekers[all-llms]

# Con servidor MCP
pip install skill-seekers[mcp]

# Todo incluido
pip install skill-seekers[all]
```

**¿Necesitas ayuda para elegir?** Ejecuta el asistente de configuración:
```bash
skill-seekers-setup
```

### Opciones de instalación

| Instalación | Funcionalidades |
|-------------|-----------------|
| `pip install skill-seekers` | Extracción, análisis de GitHub, PDF, todas las plataformas |
| `pip install skill-seekers[gemini]` | + Soporte para Google Gemini |
| `pip install skill-seekers[openai]` | + Soporte para OpenAI ChatGPT |
| `pip install skill-seekers[all-llms]` | + Todas las plataformas LLM |
| `pip install skill-seekers[mcp]` | + Servidor MCP para Claude Code, Cursor, etc. |
| `pip install skill-seekers[video]` | + Extracción de transcripciones y metadatos de YouTube/Vimeo |
| `pip install skill-seekers[video-full]` | + Transcripción Whisper y extracción visual de fotogramas |
| `pip install skill-seekers[jupyter]` | + Soporte para Jupyter Notebook |
| `pip install skill-seekers[pptx]` | + Soporte para PowerPoint |
| `pip install skill-seekers[confluence]` | + Soporte para wiki de Confluence |
| `pip install skill-seekers[notion]` | + Soporte para páginas de Notion |
| `pip install skill-seekers[rss]` | + Soporte para feeds RSS/Atom |
| `pip install skill-seekers[chat]` | + Soporte para exportación de chat de Slack/Discord |
| `pip install skill-seekers[asciidoc]` | + Soporte para documentos AsciiDoc |
| `pip install skill-seekers[all]` | Todo habilitado |

> **Dependencias visuales para video (detección de GPU):** Después de instalar `skill-seekers[video-full]`, ejecuta
> `skill-seekers video --setup` para detectar automáticamente tu GPU e instalar la variante correcta de PyTorch
> + easyocr. Esta es la forma recomendada de instalar las dependencias de extracción visual.

---

## 🚀 Flujo de trabajo de instalación con un solo comando

**La forma más rápida de ir desde la configuración hasta el skill subido - automatización completa:**

```bash
# Instalar skill de React desde las configuraciones oficiales (se sube automáticamente a Claude)
skill-seekers install --config react

# Instalar desde archivo de configuración local
skill-seekers install --config configs/custom.json

# Instalar sin subir (solo empaquetar)
skill-seekers install --config django --no-upload

# Previsualizar flujo de trabajo sin ejecutar
skill-seekers install --config react --dry-run
```

**Tiempo:** 20–45 minutos en total | **Calidad:** Listo para producción (9/10) | **Costo:** Gratis

**Fases ejecutadas:**
```
📥 FASE 1: Obtener configuración (si se proporciona nombre de configuración)
📖 FASE 2: Extraer documentación
✨ FASE 3: Mejora con IA (OBLIGATORIA - sin opción de omitir)
📦 FASE 4: Empaquetar skill
☁️  FASE 5: Subir a Claude (opcional, requiere API key)
```

**Requisitos:**
- Variable de entorno ANTHROPIC_API_KEY (para subida automática)
- Plan Claude Code Max (para mejora local con IA)

---

## 📊 Matriz de funcionalidades

Skill Seekers soporta **12 plataformas LLM**, **17 tipos de fuentes** y paridad total de funcionalidades en todos los destinos.

**Plataformas:** Claude AI, Google Gemini, OpenAI ChatGPT, MiniMax AI, Markdown genérico, OpenCode, Kimi, DeepSeek, Qwen, OpenRouter, Together AI, Fireworks AI
**Tipos de fuentes:** Sitios web de documentación, repos de GitHub, PDFs, Word (.docx), EPUB, Video, Bases de código locales, Jupyter Notebooks, HTML local, OpenAPI/Swagger, AsciiDoc, PowerPoint (.pptx), feeds RSS/Atom, páginas de manual, wikis de Confluence, páginas de Notion, exportaciones de chat de Slack/Discord

Consulta la [Matriz completa de funcionalidades](docs/FEATURE_MATRIX.md) para información detallada de soporte por plataforma y funcionalidad.

### Comparación rápida de plataformas

| Funcionalidad | Claude | Gemini | OpenAI | Markdown |
|---------------|--------|--------|--------|----------|
| Formato | ZIP + YAML | tar.gz | ZIP + Vector | ZIP |
| Carga | ✅ API | ✅ API | ✅ API | ❌ Manual |
| Mejora | ✅ Sonnet 4 | ✅ 2.0 Flash | ✅ GPT-4o | ❌ Ninguna |
| Todos los modos de skill | ✅ | ✅ | ✅ | ✅ |

---

## Ejemplos de uso

### Extracción de documentación

```bash
# Extraer sitio web de documentación
skill-seekers scrape --config configs/react.json

# Extracción rápida sin configuración
skill-seekers scrape --url https://react.dev --name react

# Con modo asíncrono (3x más rápido)
skill-seekers scrape --config configs/godot.json --async --workers 8
```

### Extracción de PDF

```bash
# Extracción básica de PDF
skill-seekers pdf --pdf docs/manual.pdf --name myskill

# Funciones avanzadas
skill-seekers pdf --pdf docs/manual.pdf --name myskill \
    --extract-tables \        # Extraer tablas
    --parallel \              # Procesamiento paralelo rápido
    --workers 8               # Usar 8 núcleos de CPU

# PDFs escaneados (requiere: pip install pytesseract Pillow)
skill-seekers pdf --pdf docs/scanned.pdf --name myskill --ocr
```

### Extracción de video

```bash
# Instalar soporte para video
pip install skill-seekers[video]        # Transcripciones + metadatos
pip install skill-seekers[video-full]   # + Whisper + extracción visual de fotogramas

# Detectar GPU automáticamente e instalar dependencias visuales (PyTorch + easyocr)
skill-seekers video --setup

# Extraer de video de YouTube
skill-seekers video --url https://www.youtube.com/watch?v=dQw4w9WgXcQ --name mytutorial

# Extraer de una lista de reproducción de YouTube
skill-seekers video --playlist https://www.youtube.com/playlist?list=... --name myplaylist

# Extraer de un archivo de video local
skill-seekers video --video-file recording.mp4 --name myrecording

# Extraer con análisis visual de fotogramas (requiere dependencias video-full)
skill-seekers video --url https://www.youtube.com/watch?v=... --name mytutorial --visual

# Con mejora por IA (limpia OCR + genera SKILL.md pulido)
skill-seekers video --url https://www.youtube.com/watch?v=... --visual --enhance-level 2

# Recortar una sección específica de un video (soporta segundos, MM:SS, HH:MM:SS)
skill-seekers video --url https://www.youtube.com/watch?v=... --start-time 1:30 --end-time 5:00

# Usar Vision API para fotogramas OCR de baja confianza (requiere ANTHROPIC_API_KEY)
skill-seekers video --url https://www.youtube.com/watch?v=... --visual --vision-ocr

# Reconstruir skill desde datos previamente extraídos (saltar descarga)
skill-seekers video --from-json output/mytutorial/video_data/extracted_data.json --name mytutorial
```

> **Guía completa:** Consulta [docs/VIDEO_GUIDE.md](docs/VIDEO_GUIDE.md) para la referencia CLI completa,
> detalles del pipeline visual, opciones de mejora con IA y solución de problemas.

### Análisis de repositorios de GitHub

```bash
# Extracción básica de repositorio
skill-seekers github --repo facebook/react

# Con autenticación (límites de tasa más altos)
export GITHUB_TOKEN=ghp_your_token_here
skill-seekers github --repo facebook/react

# Personalizar qué incluir
skill-seekers github --repo django/django \
    --include-issues \        # Extraer GitHub Issues
    --max-issues 100 \        # Limitar cantidad de issues
    --include-changelog       # Extraer CHANGELOG.md
```

### Extracción unificada multi-fuente

**Combina documentación + GitHub + PDF en un solo skill unificado con detección de conflictos:**

```bash
# Usar configuraciones unificadas existentes
skill-seekers unified --config configs/react_unified.json
skill-seekers unified --config configs/django_unified.json

# O crear configuración unificada
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

**La detección de conflictos encuentra automáticamente:**
- 🔴 **Falta en el código** (alto): Documentado pero no implementado
- 🟡 **Falta en la documentación** (medio): Implementado pero no documentado
- ⚠️ **Discrepancia de firma**: Parámetros/tipos diferentes
- ℹ️ **Discrepancia de descripción**: Explicaciones diferentes

**Guía completa:** Consulta [docs/UNIFIED_SCRAPING.md](docs/UNIFIED_SCRAPING.md) para documentación completa.

### Repositorios de configuración privados

**Comparte configuraciones personalizadas entre equipos usando repositorios git privados:**

```bash
# Opción 1: Usando herramientas MCP (recomendado)
# Registrar el repo privado de tu equipo
add_config_source(
    name="team",
    git_url="https://github.com/mycompany/skill-configs.git",
    token_env="GITHUB_TOKEN"
)

# Obtener configuración del repo del equipo
fetch_config(source="team", config_name="internal-api")
```

**Plataformas soportadas:**
- GitHub (`GITHUB_TOKEN`), GitLab (`GITLAB_TOKEN`), Gitea (`GITEA_TOKEN`), Bitbucket (`BITBUCKET_TOKEN`)

**Guía completa:** Consulta [docs/GIT_CONFIG_SOURCES.md](docs/GIT_CONFIG_SOURCES.md) para documentación completa.

## Cómo funciona

```mermaid
graph LR
    A[Sitio web de documentación] --> B[Skill Seekers]
    B --> C[Scraper]
    B --> D[Mejora con IA]
    B --> E[Empaquetador]
    C --> F[Referencias organizadas]
    D --> F
    F --> E
    E --> G[Claude Skill .zip]
    G --> H[Subir a Claude AI]
```

0. **Detectar llms.txt** - Primero verifica llms-full.txt, llms.txt, llms-small.txt
1. **Extraer**: Extrae todas las páginas de la documentación
2. **Categorizar**: Organiza el contenido en temas (API, guías, tutoriales, etc.)
3. **Mejorar**: La IA analiza los docs y crea un SKILL.md completo con ejemplos
4. **Empaquetar**: Agrupa todo en un archivo `.zip` listo para Claude

## 📋 Prerrequisitos

**Antes de empezar, asegúrate de tener:**

1. **Python 3.10 o superior** - [Descargar](https://www.python.org/downloads/) | Verificar: `python3 --version`
2. **Git** - [Descargar](https://git-scm.com/) | Verificar: `git --version`
3. **15–30 minutos** para la configuración inicial

**¿Primera vez?** → **[Empieza aquí: Guía de inicio rápido a prueba de fallos](BULLETPROOF_QUICKSTART.md)** 🎯

---

## 📤 Subir skills a Claude

Una vez empaquetado tu skill, necesitas subirlo a Claude:

### Opción 1: Subida automática (basada en API)

```bash
# Configurar tu API key (una sola vez)
export ANTHROPIC_API_KEY=sk-ant-...

# Empaquetar y subir automáticamente
skill-seekers package output/react/ --upload

# O subir un .zip existente
skill-seekers upload output/react.zip
```

### Opción 2: Subida manual (sin API Key)

```bash
# Empaquetar skill
skill-seekers package output/react/
# → Crea output/react.zip

# Luego subir manualmente:
# - Ve a https://claude.ai/skills
# - Haz clic en "Upload Skill"
# - Selecciona output/react.zip
```

### Opción 3: MCP (Claude Code)

```
En Claude Code, simplemente pide:
"Empaqueta y sube el skill de React"
```

---

## 🤖 Instalación en agentes de IA

Skill Seekers puede instalar automáticamente skills en 18 agentes de programación con IA.

```bash
# Instalar en un agente específico
skill-seekers install-agent output/react/ --agent cursor

# Instalar en todos los agentes a la vez
skill-seekers install-agent output/react/ --agent all

# Previsualizar sin instalar
skill-seekers install-agent output/react/ --agent cursor --dry-run
```

### Agentes soportados

| Agente | Ruta | Tipo |
|--------|------|------|
| **Claude Code** | `~/.claude/skills/` | Global |
| **Cursor** | `.cursor/skills/` | Proyecto |
| **VS Code / Copilot** | `.github/skills/` | Proyecto |
| **Amp** | `~/.amp/skills/` | Global |
| **Goose** | `~/.config/goose/skills/` | Global |
| **OpenCode** | `~/.opencode/skills/` | Global |
| **Windsurf** | `~/.windsurf/skills/` | Global |
| **Roo Code** | `.roo/skills/` | Proyecto |
| **Cline** | `.cline/skills/` | Proyecto |
| **Aider** | `~/.aider/skills/` | Global |
| **Bolt** | `.bolt/skills/` | Proyecto |
| **Kilo Code** | `.kilo/skills/` | Proyecto |
| **Continue** | `~/.continue/skills/` | Global |
| **Kimi Code** | `~/.kimi/skills/` | Global |

---

## 🔌 Integración MCP (26 herramientas)

Skill Seekers incluye un servidor MCP para usar desde Claude Code, Cursor, Windsurf, VS Code + Cline o IntelliJ IDEA.

```bash
# Modo stdio (Claude Code, VS Code + Cline)
python -m skill_seekers.mcp.server_fastmcp

# Modo HTTP (Cursor, Windsurf, IntelliJ)
python -m skill_seekers.mcp.server_fastmcp --transport http --port 8765

# Auto-configurar todos los agentes a la vez
./setup_mcp.sh
```

**Las 26 herramientas disponibles:**
- **Core (9):** `list_configs`, `generate_config`, `validate_config`, `estimate_pages`, `scrape_docs`, `package_skill`, `upload_skill`, `enhance_skill`, `install_skill`
- **Extendidas (10):** `scrape_github`, `scrape_pdf`, `unified_scrape`, `merge_sources`, `detect_conflicts`, `add_config_source`, `fetch_config`, `list_config_sources`, `remove_config_source`, `split_config`
- **Bases de datos vectoriales (4):** `export_to_chroma`, `export_to_weaviate`, `export_to_faiss`, `export_to_qdrant`
- **Nube (3):** `cloud_upload`, `cloud_download`, `cloud_list`

**Guía completa:** [docs/MCP_SETUP.md](docs/MCP_SETUP.md)

---

## ⚙️ Configuración

### Presets disponibles (más de 24)

```bash
# Listar todos los presets
skill-seekers list-configs
```

| Categoría | Presets |
|-----------|---------|
| **Frameworks Web** | `react`, `vue`, `angular`, `svelte`, `nextjs` |
| **Python** | `django`, `flask`, `fastapi`, `sqlalchemy`, `pytest` |
| **Desarrollo de juegos** | `godot`, `pygame`, `unity` |
| **Herramientas y DevOps** | `docker`, `kubernetes`, `terraform`, `ansible` |
| **Unificados (Docs + GitHub)** | `react-unified`, `vue-unified`, `nextjs-unified` y más |

### Crear tu propia configuración

```bash
# Opción 1: Interactivo
skill-seekers scrape --interactive

# Opción 2: Copiar y editar un preset
cp configs/react.json configs/myframework.json
nano configs/myframework.json
skill-seekers scrape --config configs/myframework.json
```

### Estructura del archivo de configuración

```json
{
  "name": "myframework",
  "description": "Cuándo usar este skill",
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

### Dónde almacenar las configuraciones

La herramienta busca en este orden:
1. Ruta exacta proporcionada
2. `./configs/` (directorio actual)
3. `~/.config/skill-seekers/configs/` (directorio de configuración del usuario)
4. API de SkillSeekersWeb.com (configuraciones predefinidas)

---

## 📊 Lo que se crea

```
output/
├── godot_data/              # Datos sin procesar extraídos
│   ├── pages/              # Archivos JSON (uno por página)
│   └── summary.json        # Resumen general
│
└── godot/                   # El skill
    ├── SKILL.md            # Mejorado con ejemplos reales
    ├── references/         # Docs categorizados
    │   ├── index.md
    │   ├── getting_started.md
    │   ├── scripting.md
    │   └── ...
    ├── scripts/            # Vacío (añade los tuyos)
    └── assets/             # Vacío (añade los tuyos)
```

---

## 🐛 Solución de problemas

### ¿No se extrajo contenido?
- Verifica tu selector `main_content`
- Prueba con: `article`, `main`, `div[role="main"]`

### ¿Los datos existen pero no se usan?
```bash
# Forzar re-extracción
rm -rf output/myframework_data/
skill-seekers scrape --config configs/myframework.json
```

### ¿Categorías incorrectas?
Edita la sección `categories` de la configuración con mejores palabras clave.

### ¿Quieres actualizar la documentación?
```bash
# Eliminar datos antiguos y volver a extraer
rm -rf output/godot_data/
skill-seekers scrape --config configs/godot.json
```

### ¿La mejora no funciona?
```bash
# Verificar si la API key está configurada
echo $ANTHROPIC_API_KEY

# Probar modo LOCAL (usa Claude Code Max, no requiere API key)
skill-seekers enhance output/react/ --mode LOCAL

# Monitorear el estado de mejora en segundo plano
skill-seekers enhance-status output/react/ --watch
```

### ¿Problemas con límite de tasa de GitHub?
```bash
# Configurar un token de GitHub (5000 req/hora vs 60/hora anónimo)
export GITHUB_TOKEN=ghp_your_token_here

# O configurar múltiples perfiles
skill-seekers config --github
```

---

## 📈 Rendimiento

| Tarea | Tiempo | Notas |
|-------|--------|-------|
| Extracción (síncrona) | 15–45 min | Solo la primera vez, basado en hilos |
| Extracción (asíncrona) | 5–15 min | 2–3x más rápido con el flag `--async` |
| Construcción | 1–3 min | Reconstrucción rápida desde caché |
| Reconstrucción | <1 min | Con `--skip-scrape` |
| Mejora (LOCAL) | 30–60 seg | Usa Claude Code Max |
| Mejora (API) | 20–40 seg | Requiere API key |
| Video (transcripción) | 1–3 min | YouTube/local, solo transcripción |
| Video (visual) | 5–15 min | + Extracción de fotogramas OCR |
| Empaquetado | 5–10 seg | Creación del .zip final |

---

## 📚 Documentación

### Primeros pasos
- **[BULLETPROOF_QUICKSTART.md](BULLETPROOF_QUICKSTART.md)** - 🎯 **¡EMPIEZA AQUÍ si eres nuevo!**
- **[QUICKSTART.md](QUICKSTART.md)** - Inicio rápido para usuarios experimentados
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problemas comunes y soluciones
- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Hoja de referencia rápida

### Guías
- **[docs/LARGE_DOCUMENTATION.md](docs/LARGE_DOCUMENTATION.md)** - Manejar documentos de 10K–40K+ páginas
- **[ASYNC_SUPPORT.md](ASYNC_SUPPORT.md)** - Guía de modo asíncrono (2–3x más rápido)
- **[docs/ENHANCEMENT_MODES.md](docs/ENHANCEMENT_MODES.md)** - Guía de modos de mejora con IA
- **[docs/MCP_SETUP.md](docs/MCP_SETUP.md)** - Configuración de integración MCP
- **[docs/UNIFIED_SCRAPING.md](docs/UNIFIED_SCRAPING.md)** - Extracción multi-fuente
- **[docs/VIDEO_GUIDE.md](docs/VIDEO_GUIDE.md)** - Guía de extracción de video

### Guías de integración
- **[docs/integrations/LANGCHAIN.md](docs/integrations/LANGCHAIN.md)** - LangChain RAG
- **[docs/integrations/CURSOR.md](docs/integrations/CURSOR.md)** - Cursor IDE
- **[docs/integrations/WINDSURF.md](docs/integrations/WINDSURF.md)** - Windsurf IDE
- **[docs/integrations/CLINE.md](docs/integrations/CLINE.md)** - Cline (VS Code)
- **[docs/integrations/RAG_PIPELINES.md](docs/integrations/RAG_PIPELINES.md)** - Todos los pipelines RAG

---

## 📝 Licencia

Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles

---

¡Feliz construcción de skills! 🚀

---

## 🔒 Seguridad

[![Insignia de evaluación de seguridad MseeP.ai](https://mseep.net/pr/yusufkaraaslan-skill-seekers-badge.png)](https://mseep.ai/app/yusufkaraaslan-skill-seekers)
