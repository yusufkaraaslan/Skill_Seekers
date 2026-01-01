export interface Template {
  id: string
  name: string
  description: string
  icon: string
  content: string
}

export const templates: Template[] = [
  {
    id: 'meeting-notes',
    name: '會議記錄',
    description: '團隊會議的標準模板，包含議程和行動項目',
    icon: '📋',
    content: `<h1>會議記錄</h1>
<p><strong>日期：</strong>${new Date().toLocaleDateString('zh-TW')}</p>
<p><strong>參與者：</strong>[姓名1]、[姓名2]</p>

<h2>議程</h2>
<ul>
  <li>議題 1</li>
  <li>議題 2</li>
  <li>議題 3</li>
</ul>

<h2>討論要點</h2>
<p>在此記錄討論內容...</p>

<h2>行動項目</h2>
<ul data-type="taskList">
  <li data-type="taskItem" data-checked="false">任務 1（負責人：@xxx）</li>
  <li data-type="taskItem" data-checked="false">任務 2（負責人：@xxx）</li>
</ul>

<h2>下次會議</h2>
<p><strong>時間：</strong>[待定]</p>`,
  },
  {
    id: 'daily-journal',
    name: '每日日誌',
    description: '追蹤每日進度、想法和任務',
    icon: '📓',
    content: `<h1>每日日誌：${new Date().toLocaleDateString('zh-TW')}</h1>

<h3>🧠 心情 / 精力</h3>
<p>今天感覺如何？</p>

<h3>✅ 今日三大優先事項</h3>
<ol>
  <li></li>
  <li></li>
  <li></li>
</ol>

<h3>📝 筆記與反思</h3>
<p>在此寫下你的想法...</p>

<h3>🙏 感恩事項</h3>
<p>今天值得感謝的事...</p>`,
  },
  {
    id: 'project-plan',
    name: '專案計劃',
    description: '新專案的大綱，包含目標和里程碑',
    icon: '🎯',
    content: `<h1>專案計劃：[專案名稱]</h1>

<h2>概述</h2>
<p>專案的簡要描述及其目標。</p>

<h2>目標</h2>
<ul>
  <li>目標 1</li>
  <li>目標 2</li>
  <li>目標 3</li>
</ul>

<h2>里程碑</h2>
<ul>
  <li><strong>階段 1：</strong>[日期] - 描述</li>
  <li><strong>階段 2：</strong>[日期] - 描述</li>
  <li><strong>階段 3：</strong>[日期] - 描述</li>
</ul>

<h2>所需資源</h2>
<p>成功需要什麼？</p>

<h2>風險與對策</h2>
<p>潛在風險及應對措施...</p>`,
  },
  {
    id: 'bug-report',
    name: '問題報告',
    description: '報告技術問題的結構化模板',
    icon: '🐛',
    content: `<h1>問題報告：[問題名稱]</h1>

<h3>描述</h3>
<p>發生了什麼？</p>

<h3>重現步驟</h3>
<ol>
  <li>步驟 1</li>
  <li>步驟 2</li>
  <li>步驟 3</li>
</ol>

<h3>預期行為</h3>
<p>應該發生什麼？</p>

<h3>實際行為</h3>
<p>實際發生了什麼？</p>

<h3>環境</h3>
<ul>
  <li>作業系統：</li>
  <li>瀏覽器：</li>
  <li>版本：</li>
</ul>

<h3>截圖/記錄</h3>
<p>如有相關截圖或日誌請附上...</p>`,
  },
  {
    id: 'learning-notes',
    name: '學習筆記',
    description: '記錄學習內容的結構化模板',
    icon: '📚',
    content: `<h1>學習筆記：[主題]</h1>
<p><strong>日期：</strong>${new Date().toLocaleDateString('zh-TW')}</p>

<h2>📌 核心概念</h2>
<ul>
  <li>概念 1</li>
  <li>概念 2</li>
</ul>

<h2>📝 詳細筆記</h2>
<p>在此寫下詳細內容...</p>

<h2>💡 重點摘要</h2>
<ul>
  <li>重點 1</li>
  <li>重點 2</li>
</ul>

<h2>❓ 問題與疑惑</h2>
<p>需要進一步研究的問題...</p>

<h2>🔗 參考資源</h2>
<ul>
  <li><a href="">資源 1</a></li>
  <li><a href="">資源 2</a></li>
</ul>`,
  },
  {
    id: 'weekly-review',
    name: '週回顧',
    description: '每週回顧與計劃模板',
    icon: '📅',
    content: `<h1>週回顧：${new Date().toLocaleDateString('zh-TW')}</h1>

<h2>🎯 本週成就</h2>
<ul>
  <li></li>
  <li></li>
  <li></li>
</ul>

<h2>📊 目標進度</h2>
<ul data-type="taskList">
  <li data-type="taskItem" data-checked="false">目標 1</li>
  <li data-type="taskItem" data-checked="false">目標 2</li>
</ul>

<h2>💭 本週反思</h2>
<p>什麼做得好？什麼可以改進？</p>

<h2>📋 下週計劃</h2>
<ul>
  <li>優先事項 1</li>
  <li>優先事項 2</li>
  <li>優先事項 3</li>
</ul>

<h2>🌟 下週目標</h2>
<p>下週最重要的目標是...</p>`,
  },
]
