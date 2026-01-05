# UI Color Optimizer Skill

> 前端 UI 配色完整指南 - 整合 Material Design、Microsoft Fluent、品牌色彩與專業配色工具

## 適用情境

當使用者需要以下協助時使用此技能：
- 選擇網站或應用程式的配色方案
- 確保色彩符合無障礙設計標準 (WCAG)
- 使用 Material Design 或 Fluent Design 色彩系統
- 參考知名品牌的官方色彩
- 建立一致的設計系統色彩規範
- 解決深色/淺色模式的配色問題

---

## 1. 色彩基礎理論

### 1.1 色彩三屬性

| 屬性 | 說明 | CSS 應用 |
|------|------|----------|
| **色相 (Hue)** | 色彩的基本類型 (0-360°) | `hsl(240, 100%, 50%)` |
| **飽和度 (Saturation)** | 色彩的純度 (0-100%) | 低飽和度 = 灰色調 |
| **明度 (Lightness)** | 色彩的亮暗程度 (0-100%) | 高明度 = 淺色 |

### 1.2 色彩搭配法則

```
互補色 (Complementary): 色輪對角 180° - 高對比、醒目
類似色 (Analogous): 相鄰 30-60° - 和諧、柔和
三等分 (Triadic): 120° 間隔 - 平衡、豐富
分裂互補 (Split-Complementary): 互補色兩側 - 對比但不刺眼
```

### 1.3 60-30-10 黃金法則

```css
:root {
  /* 60% - 主色 (背景、大面積) */
  --color-primary: #FFFFFF;

  /* 30% - 次要色 (卡片、區塊) */
  --color-secondary: #F5F5F5;

  /* 10% - 強調色 (按鈕、CTA) */
  --color-accent: #2196F3;
}
```

---

## 2. Material Design 色彩系統

### 2.1 完整色票 (Google Material Design)

#### 紅色系 (Red)
```css
--md-red-50: #FFEBEE;   --md-red-100: #FFCDD2;  --md-red-200: #EF9A9A;
--md-red-300: #E57373;  --md-red-400: #EF5350;  --md-red-500: #F44336;
--md-red-600: #E53935;  --md-red-700: #D32F2F;  --md-red-800: #C62828;
--md-red-900: #B71C1C;
/* Accent */
--md-red-A100: #FF8A80; --md-red-A200: #FF5252;
--md-red-A400: #FF1744; --md-red-A700: #D50000;
```

#### 粉紅色系 (Pink)
```css
--md-pink-50: #FCE4EC;   --md-pink-100: #F8BBD0;  --md-pink-200: #F48FB1;
--md-pink-300: #F06292;  --md-pink-400: #EC407A;  --md-pink-500: #E91E63;
--md-pink-600: #D81B60;  --md-pink-700: #C2185B;  --md-pink-800: #AD1457;
--md-pink-900: #880E4F;
/* Accent */
--md-pink-A100: #FF80AB; --md-pink-A200: #FF4081;
--md-pink-A400: #F50057; --md-pink-A700: #C51162;
```

#### 紫色系 (Purple)
```css
--md-purple-50: #F3E5F5;   --md-purple-100: #E1BEE7;  --md-purple-200: #CE93D8;
--md-purple-300: #BA68C8;  --md-purple-400: #AB47BC;  --md-purple-500: #9C27B0;
--md-purple-600: #8E24AA;  --md-purple-700: #7B1FA2;  --md-purple-800: #6A1B9A;
--md-purple-900: #4A148C;
/* Accent */
--md-purple-A100: #EA80FC; --md-purple-A200: #E040FB;
--md-purple-A400: #D500F9; --md-purple-A700: #AA00FF;
```

#### 深紫色系 (Deep Purple)
```css
--md-deep-purple-50: #EDE7F6;   --md-deep-purple-100: #D1C4E9;
--md-deep-purple-200: #B39DDB;  --md-deep-purple-300: #9575CD;
--md-deep-purple-400: #7E57C2;  --md-deep-purple-500: #673AB7;
--md-deep-purple-600: #5E35B1;  --md-deep-purple-700: #512DA8;
--md-deep-purple-800: #4527A0;  --md-deep-purple-900: #311B92;
/* Accent */
--md-deep-purple-A100: #B388FF; --md-deep-purple-A200: #7C4DFF;
--md-deep-purple-A400: #651FFF; --md-deep-purple-A700: #6200EA;
```

#### 靛藍色系 (Indigo)
```css
--md-indigo-50: #E8EAF6;   --md-indigo-100: #C5CAE9;  --md-indigo-200: #9FA8DA;
--md-indigo-300: #7986CB;  --md-indigo-400: #5C6BC0;  --md-indigo-500: #3F51B5;
--md-indigo-600: #3949AB;  --md-indigo-700: #303F9F;  --md-indigo-800: #283593;
--md-indigo-900: #1A237E;
/* Accent */
--md-indigo-A100: #8C9EFF; --md-indigo-A200: #536DFE;
--md-indigo-A400: #3D5AFE; --md-indigo-A700: #304FFE;
```

#### 藍色系 (Blue)
```css
--md-blue-50: #E3F2FD;   --md-blue-100: #BBDEFB;  --md-blue-200: #90CAF9;
--md-blue-300: #64B5F6;  --md-blue-400: #42A5F5;  --md-blue-500: #2196F3;
--md-blue-600: #1E88E5;  --md-blue-700: #1976D2;  --md-blue-800: #1565C0;
--md-blue-900: #0D47A1;
/* Accent */
--md-blue-A100: #82B1FF; --md-blue-A200: #448AFF;
--md-blue-A400: #2979FF; --md-blue-A700: #2962FF;
```

#### 淺藍色系 (Light Blue)
```css
--md-light-blue-50: #E1F5FE;   --md-light-blue-100: #B3E5FC;
--md-light-blue-200: #81D4FA;  --md-light-blue-300: #4FC3F7;
--md-light-blue-400: #29B6F6;  --md-light-blue-500: #03A9F4;
--md-light-blue-600: #039BE5;  --md-light-blue-700: #0288D1;
--md-light-blue-800: #0277BD;  --md-light-blue-900: #01579B;
/* Accent */
--md-light-blue-A100: #80D8FF; --md-light-blue-A200: #40C4FF;
--md-light-blue-A400: #00B0FF; --md-light-blue-A700: #0091EA;
```

#### 青色系 (Cyan)
```css
--md-cyan-50: #E0F7FA;   --md-cyan-100: #B2EBF2;  --md-cyan-200: #80DEEA;
--md-cyan-300: #4DD0E1;  --md-cyan-400: #26C6DA;  --md-cyan-500: #00BCD4;
--md-cyan-600: #00ACC1;  --md-cyan-700: #0097A7;  --md-cyan-800: #00838F;
--md-cyan-900: #006064;
/* Accent */
--md-cyan-A100: #84FFFF; --md-cyan-A200: #18FFFF;
--md-cyan-A400: #00E5FF; --md-cyan-A700: #00B8D4;
```

#### 藍綠色系 (Teal)
```css
--md-teal-50: #E0F2F1;   --md-teal-100: #B2DFDB;  --md-teal-200: #80CBC4;
--md-teal-300: #4DB6AC;  --md-teal-400: #26A69A;  --md-teal-500: #009688;
--md-teal-600: #00897B;  --md-teal-700: #00796B;  --md-teal-800: #00695C;
--md-teal-900: #004D40;
/* Accent */
--md-teal-A100: #A7FFEB; --md-teal-A200: #64FFDA;
--md-teal-A400: #1DE9B6; --md-teal-A700: #00BFA5;
```

#### 綠色系 (Green)
```css
--md-green-50: #E8F5E9;   --md-green-100: #C8E6C9;  --md-green-200: #A5D6A7;
--md-green-300: #81C784;  --md-green-400: #66BB6A;  --md-green-500: #4CAF50;
--md-green-600: #43A047;  --md-green-700: #388E3C;  --md-green-800: #2E7D32;
--md-green-900: #1B5E20;
/* Accent */
--md-green-A100: #B9F6CA; --md-green-A200: #69F0AE;
--md-green-A400: #00E676; --md-green-A700: #00C853;
```

#### 淺綠色系 (Light Green)
```css
--md-light-green-50: #F1F8E9;   --md-light-green-100: #DCEDC8;
--md-light-green-200: #C5E1A5;  --md-light-green-300: #AED581;
--md-light-green-400: #9CCC65;  --md-light-green-500: #8BC34A;
--md-light-green-600: #7CB342;  --md-light-green-700: #689F38;
--md-light-green-800: #558B2F;  --md-light-green-900: #33691E;
/* Accent */
--md-light-green-A100: #CCFF90; --md-light-green-A200: #B2FF59;
--md-light-green-A400: #76FF03; --md-light-green-A700: #64DD17;
```

#### 萊姆色系 (Lime)
```css
--md-lime-50: #F9FBE7;   --md-lime-100: #F0F4C3;  --md-lime-200: #E6EE9C;
--md-lime-300: #DCE775;  --md-lime-400: #D4E157;  --md-lime-500: #CDDC39;
--md-lime-600: #C0CA33;  --md-lime-700: #AFB42B;  --md-lime-800: #9E9D24;
--md-lime-900: #827717;
/* Accent */
--md-lime-A100: #F4FF81; --md-lime-A200: #EEFF41;
--md-lime-A400: #C6FF00; --md-lime-A700: #AEEA00;
```

#### 黃色系 (Yellow)
```css
--md-yellow-50: #FFFDE7;   --md-yellow-100: #FFF9C4;  --md-yellow-200: #FFF59D;
--md-yellow-300: #FFF176;  --md-yellow-400: #FFEE58;  --md-yellow-500: #FFEB3B;
--md-yellow-600: #FDD835;  --md-yellow-700: #FBC02D;  --md-yellow-800: #F9A825;
--md-yellow-900: #F57F17;
/* Accent */
--md-yellow-A100: #FFFF8D; --md-yellow-A200: #FFFF00;
--md-yellow-A400: #FFEA00; --md-yellow-A700: #FFD600;
```

#### 琥珀色系 (Amber)
```css
--md-amber-50: #FFF8E1;   --md-amber-100: #FFECB3;  --md-amber-200: #FFE082;
--md-amber-300: #FFD54F;  --md-amber-400: #FFCA28;  --md-amber-500: #FFC107;
--md-amber-600: #FFB300;  --md-amber-700: #FFA000;  --md-amber-800: #FF8F00;
--md-amber-900: #FF6F00;
/* Accent */
--md-amber-A100: #FFE57F; --md-amber-A200: #FFD740;
--md-amber-A400: #FFC400; --md-amber-A700: #FFAB00;
```

#### 橙色系 (Orange)
```css
--md-orange-50: #FFF3E0;   --md-orange-100: #FFE0B2;  --md-orange-200: #FFCC80;
--md-orange-300: #FFB74D;  --md-orange-400: #FFA726;  --md-orange-500: #FF9800;
--md-orange-600: #FB8C00;  --md-orange-700: #F57C00;  --md-orange-800: #EF6C00;
--md-orange-900: #E65100;
/* Accent */
--md-orange-A100: #FFD180; --md-orange-A200: #FFAB40;
--md-orange-A400: #FF9100; --md-orange-A700: #FF6D00;
```

#### 深橙色系 (Deep Orange)
```css
--md-deep-orange-50: #FBE9E7;   --md-deep-orange-100: #FFCCBC;
--md-deep-orange-200: #FFAB91;  --md-deep-orange-300: #FF8A65;
--md-deep-orange-400: #FF7043;  --md-deep-orange-500: #FF5722;
--md-deep-orange-600: #F4511E;  --md-deep-orange-700: #E64A19;
--md-deep-orange-800: #D84315;  --md-deep-orange-900: #BF360C;
/* Accent */
--md-deep-orange-A100: #FF9E80; --md-deep-orange-A200: #FF6E40;
--md-deep-orange-A400: #FF3D00; --md-deep-orange-A700: #DD2C00;
```

#### 棕色系 (Brown) - 無 Accent
```css
--md-brown-50: #EFEBE9;   --md-brown-100: #D7CCC8;  --md-brown-200: #BCAAA4;
--md-brown-300: #A1887F;  --md-brown-400: #8D6E63;  --md-brown-500: #795548;
--md-brown-600: #6D4C41;  --md-brown-700: #5D4037;  --md-brown-800: #4E342E;
--md-brown-900: #3E2723;
```

#### 灰色系 (Grey) - 無 Accent
```css
--md-grey-50: #FAFAFA;   --md-grey-100: #F5F5F5;  --md-grey-200: #EEEEEE;
--md-grey-300: #E0E0E0;  --md-grey-400: #BDBDBD;  --md-grey-500: #9E9E9E;
--md-grey-600: #757575;  --md-grey-700: #616161;  --md-grey-800: #424242;
--md-grey-900: #212121;
```

#### 藍灰色系 (Blue Grey) - 無 Accent
```css
--md-blue-grey-50: #ECEFF1;   --md-blue-grey-100: #CFD8DC;
--md-blue-grey-200: #B0BEC5;  --md-blue-grey-300: #90A4AE;
--md-blue-grey-400: #78909C;  --md-blue-grey-500: #607D8B;
--md-blue-grey-600: #546E7A;  --md-blue-grey-700: #455A64;
--md-blue-grey-800: #37474F;  --md-blue-grey-900: #263238;
```

### 2.2 使用建議

| 色階 | 用途 | 範例 |
|------|------|------|
| 50-100 | 背景、淺色區塊 | 卡片背景、hover 效果 |
| 200-300 | 次要元素、分隔線 | 邊框、disabled 狀態 |
| 400-600 | 主要元素 | 按鈕、連結、圖示 |
| 700-900 | 強調、文字 | 標題、重要文字 |
| A100-A700 | 強調色 | CTA 按鈕、badge |

---

## 3. Microsoft Fluent Design 色彩系統

### 3.1 核心色彩 (Fluent UI)

#### 品牌主色
```css
--fluent-brand-primary: #0078D4;  /* Microsoft 藍 */
--fluent-brand-success: #107C10;  /* 成功綠 */
--fluent-brand-warning: #FFB900;  /* 警告黃 */
--fluent-brand-error: #D13438;    /* 錯誤紅 */
```

#### 黃橙色系
```css
--fluent-yellow: #FFB900;
--fluent-orange-light: #FF8C00;
--fluent-orange: #F7630C;
--fluent-orange-dark: #DA3B01;
--fluent-rust: #CA5010;
```

#### 紅粉色系
```css
--fluent-red-light: #E74856;
--fluent-red: #E81123;
--fluent-red-dark: #D13438;
--fluent-magenta: #EA005E;
--fluent-magenta-dark: #E3008C;
--fluent-pink: #C30052;
--fluent-pink-dark: #BF0077;
--fluent-fuchsia: #C239B3;
```

#### 紫色系
```css
--fluent-purple-light: #8E8CD8;
--fluent-purple: #6B69D6;
--fluent-purple-medium: #8764B8;
--fluent-purple-dark: #744DA9;
--fluent-violet: #B146C2;
--fluent-violet-dark: #881798;
--fluent-plum: #9A0089;
```

#### 藍色系
```css
--fluent-blue-primary: #0078D7;
--fluent-blue-dark: #0063B1;
```

#### 青綠色系
```css
--fluent-cyan: #0099BC;
--fluent-cyan-dark: #2D7D9A;
--fluent-teal-light: #00B7C3;
--fluent-teal: #038387;
--fluent-teal-dark: #018574;
--fluent-mint: #00B294;
--fluent-seafoam: #00CC6A;
```

#### 綠色系
```css
--fluent-green-light: #10893E;
--fluent-green: #107C10;
--fluent-green-dark: #498205;
```

#### 中性色系
```css
--fluent-grey-warm: #7A7574;
--fluent-grey: #767676;
--fluent-grey-cool: #5D5A58;
--fluent-grey-dark: #4C4A48;
--fluent-slate: #68768A;
--fluent-steel: #69797E;
--fluent-steel-dark: #515C6B;
--fluent-charcoal: #4A5459;
```

### 3.2 深色模式適配

```css
/* Fluent 深色模式調整原則 */
:root[data-theme="dark"] {
  /* 降低飽和度，提高明度 */
  --fluent-brand-primary: #4CC2FF;  /* 淺藍取代深藍 */
  --fluent-brand-success: #6CCB5F;
  --fluent-brand-warning: #FCE100;
  --fluent-brand-error: #FF99A4;

  /* 背景色 */
  --fluent-bg-primary: #202020;
  --fluent-bg-secondary: #2D2D2D;
  --fluent-bg-tertiary: #383838;
}
```

---

## 4. 知名品牌色彩參考

### 4.1 科技公司

```css
/* Google */
--brand-google-blue: #4285F4;
--brand-google-red: #EA4335;
--brand-google-yellow: #FBBC05;
--brand-google-green: #34A853;

/* Facebook/Meta */
--brand-facebook: #1877F2;

/* Amazon */
--brand-amazon-orange: #FF9900;
--brand-amazon-blue: #146EB4;

/* Apple */
--brand-apple-blue: #147EFB;
--brand-apple-green: #53D769;
--brand-apple-yellow: #FECB2E;

/* Microsoft */
--brand-microsoft-red: #F25022;
--brand-microsoft-green: #7FBA00;
--brand-microsoft-blue: #00A4EF;
--brand-microsoft-yellow: #FFB900;

/* Discord */
--brand-discord: #5865F2;
--brand-discord-green: #57F287;
--brand-discord-yellow: #FEE75C;
--brand-discord-pink: #EB459E;
--brand-discord-red: #ED4245;

/* GitHub */
--brand-github: #333333;
--brand-github-blue: #4078C0;
--brand-github-green: #6CC644;

/* LinkedIn */
--brand-linkedin: #0A66C2;

/* Instagram 漸層 */
--brand-instagram-purple: #833AB4;
--brand-instagram-pink: #E1306C;
--brand-instagram-orange: #F56040;
```

### 4.2 台灣常用服務

```css
/* LINE */
--brand-line: #00B900;

/* 蝦皮 */
--brand-shopee: #EE4D2D;

/* PChome */
--brand-pchome: #E24C4B;

/* momo */
--brand-momo: #D5005F;

/* 全聯 */
--brand-pxmart: #E60012;
```

---

## 5. 無障礙設計 (WCAG 2.1)

### 5.1 對比度標準

| 等級 | 一般文字 | 大型文字 (18px+/14px bold+) |
|------|----------|---------------------------|
| AA (最低) | 4.5:1 | 3:1 |
| AAA (推薦) | 7:1 | 4.5:1 |

### 5.2 安全配色組合

```css
/* 高對比度組合 - AA 合規 */
.safe-combinations {
  /* 白底深色文字 */
  --text-on-white: #212121;      /* 對比度 16.1:1 */
  --link-on-white: #0D47A1;      /* 對比度 8.5:1 */

  /* 深底淺色文字 */
  --text-on-dark: #FFFFFF;       /* 對比度 21:1 on #212121 */
  --link-on-dark: #82B1FF;       /* 對比度 6.2:1 on #212121 */

  /* 品牌色上的文字 */
  --text-on-blue-500: #FFFFFF;   /* #2196F3 需白字 */
  --text-on-yellow-500: #212121; /* #FFEB3B 需深字 */
}
```

### 5.3 色盲友善設計

```css
/* 避免僅用顏色傳達資訊 */
.status-indicator {
  /* 紅綠色盲友善組合 */
  --status-success: #00897B;  /* 藍綠色取代純綠 */
  --status-error: #C62828;    /* 深紅 + 圖示輔助 */
  --status-warning: #FF8F00;  /* 橘色安全 */
  --status-info: #1565C0;     /* 藍色安全 */
}

/* 搭配圖示或文字標示 */
.error-message::before {
  content: "✕ ";  /* 加圖示 */
}
.success-message::before {
  content: "✓ ";
}
```

---

## 6. 實用配色方案範本

### 6.1 企業專業風格

```css
:root {
  /* 主色調 - 深藍專業感 */
  --color-primary: #1A237E;
  --color-primary-light: #534BAE;
  --color-primary-dark: #000051;

  /* 強調色 - 橙色行動呼籲 */
  --color-accent: #FF6D00;
  --color-accent-light: #FF9E40;
  --color-accent-dark: #C43E00;

  /* 中性色 */
  --color-background: #FAFAFA;
  --color-surface: #FFFFFF;
  --color-text-primary: #212121;
  --color-text-secondary: #757575;

  /* 狀態色 */
  --color-success: #2E7D32;
  --color-warning: #F9A825;
  --color-error: #C62828;
  --color-info: #1565C0;
}
```

### 6.2 現代科技風格

```css
:root {
  /* 漸層主色 */
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);

  /* 單色備用 */
  --color-primary: #667EEA;
  --color-secondary: #764BA2;

  /* 深色背景 */
  --color-background: #0F0F1A;
  --color-surface: #1A1A2E;
  --color-surface-elevated: #252545;

  /* 文字 */
  --color-text-primary: #FFFFFF;
  --color-text-secondary: #A0A0B0;

  /* 霓虹強調 */
  --color-neon-cyan: #00F5FF;
  --color-neon-pink: #FF00FF;
}
```

### 6.3 清新自然風格

```css
:root {
  /* 大地色系 */
  --color-primary: #2E7D32;
  --color-primary-light: #60AD5E;
  --color-primary-dark: #005005;

  /* 暖色輔助 */
  --color-secondary: #8D6E63;
  --color-accent: #FF8F00;

  /* 自然背景 */
  --color-background: #F1F8E9;
  --color-surface: #FFFFFF;
  --color-cream: #FFF8E1;

  /* 文字 */
  --color-text-primary: #33691E;
  --color-text-secondary: #689F38;
}
```

### 6.4 深色模式範本

```css
:root[data-theme="dark"] {
  /* 背景層級 */
  --color-background: #121212;     /* 最底層 */
  --color-surface: #1E1E1E;        /* 卡片 */
  --color-surface-elevated: #2D2D2D; /* 浮動元素 */
  --color-overlay: rgba(255, 255, 255, 0.05);

  /* 主色調整 (提高明度) */
  --color-primary: #BB86FC;
  --color-primary-variant: #3700B3;
  --color-secondary: #03DAC6;

  /* 文字 */
  --color-text-high: rgba(255, 255, 255, 0.87);
  --color-text-medium: rgba(255, 255, 255, 0.60);
  --color-text-disabled: rgba(255, 255, 255, 0.38);

  /* 狀態色 (降低飽和度) */
  --color-error: #CF6679;
  --color-success: #81C784;
  --color-warning: #FFD54F;
}
```

---

## 7. CSS 變數最佳實踐

### 7.1 設計系統結構

```css
:root {
  /* ========== 基礎色票 (Primitives) ========== */
  --palette-blue-50: #E3F2FD;
  --palette-blue-100: #BBDEFB;
  --palette-blue-500: #2196F3;
  --palette-blue-700: #1976D2;
  --palette-blue-900: #0D47A1;

  /* ========== 語意化色彩 (Semantic) ========== */
  --color-brand-primary: var(--palette-blue-500);
  --color-brand-primary-hover: var(--palette-blue-700);
  --color-brand-primary-active: var(--palette-blue-900);

  /* ========== 元件色彩 (Component) ========== */
  --button-primary-bg: var(--color-brand-primary);
  --button-primary-bg-hover: var(--color-brand-primary-hover);
  --button-primary-text: #FFFFFF;

  --link-color: var(--color-brand-primary);
  --link-color-hover: var(--color-brand-primary-hover);

  /* ========== 表面與背景 ========== */
  --surface-background: #FFFFFF;
  --surface-foreground: #FAFAFA;
  --surface-border: #E0E0E0;

  /* ========== 文字階層 ========== */
  --text-primary: #212121;
  --text-secondary: #757575;
  --text-disabled: #BDBDBD;
  --text-inverse: #FFFFFF;
}
```

### 7.2 深淺色切換

```css
/* 淺色主題 (預設) */
:root {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F5F5;
  --text-primary: #212121;
  --text-secondary: #757575;
  --border-color: #E0E0E0;
  --shadow-color: rgba(0, 0, 0, 0.1);
}

/* 深色主題 */
:root[data-theme="dark"],
[data-theme="dark"] {
  --bg-primary: #121212;
  --bg-secondary: #1E1E1E;
  --text-primary: #FFFFFF;
  --text-secondary: #B0B0B0;
  --border-color: #333333;
  --shadow-color: rgba(0, 0, 0, 0.5);
}

/* 自動偵測系統設定 */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg-primary: #121212;
    --bg-secondary: #1E1E1E;
    --text-primary: #FFFFFF;
    --text-secondary: #B0B0B0;
  }
}
```

### 7.3 使用範例

```css
/* 元件直接使用語意化變數 */
.card {
  background: var(--surface-background);
  border: 1px solid var(--surface-border);
  color: var(--text-primary);
}

.card-subtitle {
  color: var(--text-secondary);
}

.button-primary {
  background: var(--button-primary-bg);
  color: var(--button-primary-text);
}

.button-primary:hover {
  background: var(--button-primary-bg-hover);
}
```

---

## 8. 配色工具推薦

### 8.1 線上工具

| 工具 | 網址 | 特色 |
|------|------|------|
| **Adobe Color** | [color.adobe.com](https://color.adobe.com/zh/explore/) | 色輪、圖片取色、探索作品 |
| **Coolors** | [coolors.co](https://coolors.co/) | 空白鍵快速生成 5 色組合 |
| **Material UI Colors** | [materialui.co/colors](https://materialui.co/colors) | Material Design 完整色票 |
| **Colorist AI** | [colorist-ai.com](https://colorist-ai.com/) | AI 依產業生成配色 |
| **Paletton** | [paletton.com](https://paletton.com/) | 互動式色輪 |
| **Color Tool (Google)** | [m2.material.io/resources/color](https://m2.material.io/resources/color/) | UI 預覽配色 |
| **Canva Color** | [canva.com/colors](https://www.canva.com/colors/) | 圖片取色、配色靈感 |
| **Nippon Colors** | [nipponcolors.com](https://nipponcolors.com/) | 日本傳統色票 |
| **BrandColors** | [brandcolors.net](https://brandcolors.net/) | 600+ 品牌官方色 |

### 8.2 對比度檢測

| 工具 | 網址 | 用途 |
|------|------|------|
| **WebAIM Contrast Checker** | [webaim.org/resources/contrastchecker](https://webaim.org/resources/contrastchecker/) | WCAG 對比度檢測 |
| **Contrast Ratio** | [contrast-ratio.com](https://contrast-ratio.com/) | 即時對比度計算 |
| **Accessible Colors** | [accessible-colors.com](https://accessible-colors.com/) | 自動建議符合 AA 的顏色 |

### 8.3 漸層工具

| 工具 | 網址 | 特色 |
|------|------|------|
| **CSS Gradient** | [cssgradient.io](https://cssgradient.io/) | 視覺化漸層編輯器 |
| **Grabient** | [grabient.com](https://www.grabient.com/) | 現成漸層配方 |
| **UI Gradients** | [uigradients.com](https://uigradients.com/) | 精選漸層收藏 |

---

## 9. 快速參考表

### 9.1 常用配色決策

```
Q: 按鈕該用什麼顏色?
A: 主要 CTA → 品牌主色 (500-600)
   次要動作 → 灰色或透明
   危險操作 → 紅色系

Q: 文字顏色怎麼選?
A: 主文字 → Grey 800-900 (淺底) / White 87% (深底)
   副標題 → Grey 600-700 / White 60%
   提示文字 → Grey 400-500 / White 38%

Q: 背景該用什麼色?
A: 主背景 → 純白或 Grey 50
   卡片 → 純白
   區塊分隔 → Grey 100-200

Q: 連結顏色?
A: 預設 → Blue 700
   Hover → Blue 900
   已訪問 → Purple 700 (可選)
```

### 9.2 深色模式速查

```
淺 → 深 轉換規則:
背景: #FFFFFF → #121212
表面: #FAFAFA → #1E1E1E
卡片: #FFFFFF → #2D2D2D

主色調整:
飽和度 -10~20%
明度 +20~40%

文字透明度:
高強調: 87%
中等: 60%
禁用: 38%
```

### 9.3 WCAG 安全組合

```css
/* 100% 安全的文字配色 */
.safe-text {
  /* 白底 */
  color: #1A1A1A;  /* 對比度 17.4:1 */

  /* 深底 (#121212) */
  color: #E0E0E0;  /* 對比度 12.6:1 */
}

/* 安全的連結色 */
.safe-link {
  /* 白底 */
  color: #0D47A1;  /* 對比度 8.5:1 */

  /* 深底 */
  color: #90CAF9;  /* 對比度 8.3:1 */
}
```

---

## 10. 資料來源

- [Material Design Color System](https://materialui.co/colors) - Google Material Design 完整色票
- [Microsoft Fluent 2 Design System](https://fluent2.microsoft.design/color) - Microsoft Fluent 色彩系統
- [BrandColors](https://brandcolors.net/) - 品牌官方色彩資料庫
- [HTMLColors Fluent Colors](https://htmlcolors.com/fluent-colors) - Fluent Design 48 色
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/) - 無障礙設計標準
- [配色工具推薦 - Out of Design](https://out-of-design.com/index.php/2023/04/13/color-tools/)
- [六個配色網站 - RAB.TW](https://rab.tw/six-websites-of-color-scheme/)
