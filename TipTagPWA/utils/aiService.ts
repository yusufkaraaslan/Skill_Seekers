export enum AISuggestionType {
  FIX_GRAMMAR = '修正文法',
  SUMMARIZE = '摘要',
  EXPAND = '繼續撰寫',
  REPHRASE = '改寫',
  GENERATE_IDEAS = '產生想法',
  TRANSLATE_EN = '翻譯為英文',
  TRANSLATE_ZH = '翻譯為中文',
}

// AI Service using browser-based API or fallback
// Can be configured to use OpenAI, Anthropic, Gemini, or local models

interface AIConfig {
  provider: 'openai' | 'anthropic' | 'gemini' | 'local'
  apiKey?: string
  model?: string
}

let aiConfig: AIConfig = {
  provider: 'local',
}

export function setAIConfig(config: Partial<AIConfig>) {
  aiConfig = { ...aiConfig, ...config }
  if (typeof window !== 'undefined') {
    localStorage.setItem('tiptag_ai_config', JSON.stringify(aiConfig))
  }
}

export function getAIConfig(): AIConfig {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('tiptag_ai_config')
    if (stored) {
      try {
        aiConfig = JSON.parse(stored)
      } catch {
        // Use default
      }
    }
  }
  return aiConfig
}

function getPromptForType(type: AISuggestionType, text: string): string {
  switch (type) {
    case AISuggestionType.FIX_GRAMMAR:
      return `修正以下文字的文法和拼寫錯誤，不要改變原意。只回傳修正後的文字：\n\n"${text}"`
    case AISuggestionType.SUMMARIZE:
      return `用簡潔的一段話摘要以下內容：\n\n"${text}"`
    case AISuggestionType.EXPAND:
      return `根據以下內容繼續撰寫，保持相同的語氣和風格：\n\n"${text}"`
    case AISuggestionType.REPHRASE:
      return `改寫以下文字，使其更專業、清晰：\n\n"${text}"`
    case AISuggestionType.GENERATE_IDEAS:
      return `根據這個主題產生 5 個創意想法或要點：\n\n"${text}"`
    case AISuggestionType.TRANSLATE_EN:
      return `將以下內容翻譯成英文，保持原意：\n\n"${text}"`
    case AISuggestionType.TRANSLATE_ZH:
      return `將以下內容翻譯成繁體中文，保持原意：\n\n"${text}"`
    default:
      return text
  }
}

export async function generateAIContent(
  type: AISuggestionType,
  contextText: string
): Promise<string> {
  const config = getAIConfig()
  const prompt = getPromptForType(type, contextText)

  // If no API key configured, use simple local transformations
  if (config.provider === 'local' || !config.apiKey) {
    return localTransform(type, contextText)
  }

  try {
    switch (config.provider) {
      case 'openai':
        return await callOpenAI(prompt, config.apiKey!, config.model || 'gpt-4o-mini')
      case 'anthropic':
        return await callAnthropic(prompt, config.apiKey!, config.model || 'claude-3-haiku-20240307')
      case 'gemini':
        return await callGemini(prompt, config.apiKey!, config.model || 'gemini-1.5-flash')
      default:
        return localTransform(type, contextText)
    }
  } catch (error) {
    console.error('AI API Error:', error)
    throw new Error('無法產生內容，請稍後再試。')
  }
}

async function callOpenAI(prompt: string, apiKey: string, model: string): Promise<string> {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 2000,
    }),
  })

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.status}`)
  }

  const data = await response.json()
  return data.choices[0]?.message?.content || ''
}

async function callAnthropic(prompt: string, apiKey: string, model: string): Promise<string> {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model,
      max_tokens: 2000,
      messages: [{ role: 'user', content: prompt }],
    }),
  })

  if (!response.ok) {
    throw new Error(`Anthropic API error: ${response.status}`)
  }

  const data = await response.json()
  return data.content[0]?.text || ''
}

async function callGemini(prompt: string, apiKey: string, model: string): Promise<string> {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
      }),
    }
  )

  if (!response.ok) {
    throw new Error(`Gemini API error: ${response.status}`)
  }

  const data = await response.json()
  return data.candidates?.[0]?.content?.parts?.[0]?.text || ''
}

// Simple local transformations without AI
function localTransform(type: AISuggestionType, text: string): string {
  switch (type) {
    case AISuggestionType.FIX_GRAMMAR:
      // Basic cleanup
      return text.trim().replace(/\s+/g, ' ')
    case AISuggestionType.SUMMARIZE:
      // Take first 100 chars as simple summary
      const words = text.split(/\s+/).slice(0, 30).join(' ')
      return words + (text.split(/\s+/).length > 30 ? '...' : '')
    case AISuggestionType.EXPAND:
      return text + '\n\n[請配置 AI API 以啟用自動撰寫功能]'
    case AISuggestionType.REPHRASE:
      return text // Would need AI for actual rephrasing
    case AISuggestionType.GENERATE_IDEAS:
      return `相關想法：
• 想法 1：[請配置 AI API]
• 想法 2：[請配置 AI API]
• 想法 3：[請配置 AI API]`
    case AISuggestionType.TRANSLATE_EN:
      return '[請配置 AI API 以啟用翻譯功能]\n\n' + text
    case AISuggestionType.TRANSLATE_ZH:
      return '[請配置 AI API 以啟用翻譯功能]\n\n' + text
    default:
      return text
  }
}
