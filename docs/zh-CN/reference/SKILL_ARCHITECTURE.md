# 技能架构指南：分层与拆分

使用路由器/分发器模式构建复杂多技能系统的完整指南。

---

## 目录

- [概述](#overview)
- [何时拆分技能](#when-to-split-skills)
- [路由器模式](#the-router-pattern)
- [手动技能架构](#manual-skill-architecture)
- [最佳实践](#best-practices)
- [完整示例](#complete-examples)
- [实现指南](#implementation-guide)
- [故障排除](#troubleshooting)

---

## 概述

### 500 行指南

Claude 建议将技能文件保持在 **500 行以内**以获得最佳性能。此指南存在的原因：

- ✅ **更好的解析** - AI 可以更有效地理解聚焦的内容
- ✅ **上下文效率** - 每个任务只加载相关信息
- ✅ **可维护性** - 更易于调试、更新和管理
- ✅ **单一职责** - 每个技能做好一件事

### 单体技能的问题

随着应用变得越来越复杂，开发者常创建具有以下问题的技能：

- ❌ **超过 500 行** - 信息太多，无法有效解析
- ❌ **混合关注点** - 处理多个不相关的职责
- ❌ **浪费上下文** - 即使只有一小部分相关，也会加载整个文件
- ❌ **难以维护** - 更改需要仔细浏览大文件

### 解决方案：技能分层

**技能分层** 包括：

1. **拆分** - 将大技能拆分为聚焦的子技能
2. **路由** - 创建主技能，将查询引导到适当的子技能
3. **加载** - 每个任务只激活相关的子技能

**结果：** 在构建复杂应用的同时，保持每个技能在 500 行指南内。

---

## 何时拆分技能

### 决策矩阵

| 技能大小 | 复杂度 | 建议 |
|-----------|-----------|----------------|
| < 500 行 | 单一关注点 | ✅ **保持单体** |
| 500-1000 行 | 相关关注点 | ⚠️ **考虑拆分** |
| 1000+ 行 | 多个关注点 | ❌ **必须拆分** |

### 拆分指标

**你应该在以下情况拆分：**

- ✅ 技能超过 500 行
- ✅ 多个不同的职责（CRUD、工作流等）
- ✅ 不同的团队成员维护不同部分
- ✅ 只有部分与特定任务相关
- ✅ 频繁超出上下文窗口

**你可以在以下情况保持单体：**

- ✅ 少于 500 行
- ✅ 单一、内聚的职责
- ✅ 所有内容经常一起使用
- ✅ 简单、聚焦的用例

---

## 路由器模式

### 什么是路由器技能？

**路由器技能**（也称为**分发器**或**中心**技能）是一个轻量级主技能，它：

1. **分析** 用户的查询
2. **识别** 哪些子技能相关
3. **引导** Claude 激活适当的子技能
4. **协调** 多个子技能的响应（如需要）

### 工作原理

```
用户查询："How do I book a flight to Paris?"
     ↓
路由器技能：分析关键词 → "flight", "book"
     ↓
激活：flight_booking 子技能
     ↓
响应：仅加载此技能的航班预订指南
```

### 路由器技能结构

```markdown
# Travel Planner (Router)

## When to Use This Skill

Use for travel planning, booking, and itinerary management.

This is a router skill that directs your questions to specialized sub-skills.

## Sub-Skills Available

### flight_booking
For booking flights, searching airlines, comparing prices, seat selection.
**Keywords:** flight, airline, booking, ticket, departure, arrival

### hotel_reservation
For hotel search, room booking, amenities, check-in/check-out.
**Keywords:** hotel, accommodation, room, reservation, stay

### itinerary_generation
For creating travel plans, scheduling activities, route optimization.
**Keywords:** itinerary, schedule, plan, activities, route

## Routing Logic

Based on your question keywords:
- Flight-related → Activate `flight_booking`
- Hotel-related → Activate `hotel_reservation`
- Planning-related → Activate `itinerary_generation`
- Multiple topics → Activate relevant combination

## Usage Examples

**"Find me a flight to Paris"** → flight_booking
**"Book hotel in Tokyo"** → hotel_reservation
**"Create 5-day Rome itinerary"** → itinerary_generation
**"Plan Paris trip with flights and hotel"** → flight_booking + hotel_reservation + itinerary_generation
```

---

## 手动技能架构

### 示例 1：电商平台

**问题：** 电商技能有 2000+ 行，涵盖目录、购物车、结账、订单和管理。

**解决方案：** 拆分为带路由器的聚焦子技能。

#### 子技能

**1. `ecommerce.md`（路由器 - 150 行）**
```markdown
# E-Commerce Platform (Router)

## Sub-Skills
- product_catalog - Browse, search, filter products
- shopping_cart - Add/remove items, quantities
- checkout_payment - Process orders, payments
- order_management - Track orders, returns
- admin_tools - Inventory, analytics

## Routing
product/catalog/search → product_catalog
cart/basket/add/remove → shopping_cart
checkout/payment/billing → checkout_payment
order/track/return → order_management
admin/inventory/analytics → admin_tools
```

**2. `product_catalog.md`（350 行）**
```markdown
# Product Catalog

## When to Use
Product browsing, searching, filtering, recommendations.

## Quick Reference
- Search products: `search(query, filters)`
- Get details: `getProduct(id)`
- Filter: `filter(category, price, brand)`
...
```

**3. `shopping_cart.md`（280 行）**
```markdown
# Shopping Cart

## When to Use
Managing cart items, quantities, totals.

## Quick Reference
- Add item: `cart.add(productId, quantity)`
- Update quantity: `cart.update(itemId, quantity)`
...
```

**结果：**
- 路由器：150 行 ✅
- 每个子技能：200-400 行 ✅
- 总功能：不变
- 上下文效率：5 倍提升

---

### 示例 2：代码助手

**问题：** 代码助手处理调试、重构、文档、测试 - 1800+ 行。

**解决方案：** 带智能路由的专门子技能。

#### 架构

```
code_assistant.md (Router - 200 lines)
├── debugging.md (450 lines)
├── refactoring.md (380 lines)
├── documentation.md (320 lines)
└── testing.md (400 lines)
```

#### 路由器逻辑

```markdown
# Code Assistant (Router)

## Routing Keywords

### debugging
error, bug, exception, crash, fix, troubleshoot, debug

### refactoring
refactor, clean, optimize, simplify, restructure, improve

### documentation
docs, comment, docstring, readme, api, explain

### testing
test, unit, integration, coverage, assert, mock
```

---

### 示例 3：数据流水线

**问题：** ETL 流水线技能涵盖提取、转换、加载、验证、监控。

**解决方案：** 流水线阶段作为子技能。

```
data_pipeline.md (Router)
├── data_extraction.md - Source connectors, API calls
├── data_transformation.md - Cleaning, mapping, enrichment
├── data_loading.md - Database writes, file exports
├── data_validation.md - Quality checks, error handling
└── pipeline_monitoring.md - Logging, alerts, metrics
```

---

## 最佳实践

### 1. 单一职责原则

**每个子技能应该只有一个明确的目的。**

❌ **不佳：** `user_management.md` 处理认证、个人资料、权限、通知
✅ **良好：**
- `user_authentication.md` - 登录、登出、会话
- `user_profiles.md` - 个人资料 CRUD
- `user_permissions.md` - 角色、访问控制
- `user_notifications.md` - 邮件、推送、提醒

### 2. 清晰的路由关键词

**使路由关键词明确且无歧义。**

❌ **不佳：** 模糊的关键词如 "data"、"user"、"process"
✅ **良好：** 具体的关键词如 "login"、"authenticate"、"extract"、"transform"

### 3. 最小化路由器复杂度

**保持路由器轻量——只包含路由逻辑。**

❌ **不佳：** 路由器包含实际的实现代码
✅ **良好：** 路由器只包含：
- 子技能描述
- 路由关键词
- 使用示例
- 无实现细节

### 4. 逻辑分组

**按职责分组，而不是按代码结构。**

❌ **不佳：** 按文件类型拆分（controllers、models、views）
✅ **良好：** 按功能拆分（user_auth、product_catalog、order_processing）

### 5. 避免过度拆分

**不要为琐碎的区别创建子技能。**

❌ **不佳：** "add_user" 和 "update_user" 的单独技能
✅ **良好：** 涵盖所有 CRUD 的单个 "user_management" 技能

### 6. 记录依赖关系

**明确说明子技能何时协同工作。**

```markdown
## Multi-Skill Operations

**Place order:** Requires coordination between:
1. product_catalog - Validate product availability
2. shopping_cart - Get cart contents
3. checkout_payment - Process payment
4. order_management - Create order record
```

### 7. 保持结构一致

**在所有子技能中使用相同的 SKILL.md 结构。**

标准章节：
```markdown
# Skill Name

## When to Use This Skill
[Clear description]

## Quick Reference
[Common operations]

## Key Concepts
[Domain terminology]

## Working with This Skill
[Usage guidance]

## Reference Files
[Documentation organization]
```

---

## 完整示例

### Travel Planner（完整实现）

#### 目录结构

```
skills/
├── travel_planner.md (Router - 180 lines)
├── flight_booking.md (420 lines)
├── hotel_reservation.md (380 lines)
├── itinerary_generation.md (450 lines)
├── travel_insurance.md (290 lines)
└── budget_tracking.md (340 lines)
```

#### travel_planner.md（路由器）

```markdown
---
name: travel_planner
description: Travel planning, booking, and itinerary management router
---

# Travel Planner (Router)

## When to Use This Skill

Use for all travel-related planning, bookings, and itinerary management.

This router skill analyzes your travel needs and activates specialized sub-skills.

## Available Sub-Skills

### flight_booking
**Purpose:** Flight search, booking, seat selection, airline comparisons
**Keywords:** flight, airline, plane, ticket, departure, arrival, airport, booking
**Use for:** Finding and booking flights, comparing prices, selecting seats

### hotel_reservation
**Purpose:** Hotel search, room booking, amenities, check-in/out
**Keywords:** hotel, accommodation, room, lodging, reservation, stay, check-in
**Use for:** Finding hotels, booking rooms, checking amenities

### itinerary_generation
**Purpose:** Travel planning, scheduling, route optimization
**Keywords:** itinerary, schedule, plan, route, activities, sightseeing
**Use for:** Creating day-by-day plans, organizing activities

### travel_insurance
**Purpose:** Travel insurance options, coverage, claims
**Keywords:** insurance, coverage, protection, medical, cancellation, claim
**Use for:** Insurance recommendations, comparing policies

### budget_tracking
**Purpose:** Travel budget planning, expense tracking
**Keywords:** budget, cost, expense, price, spending, money
**Use for:** Estimating costs, tracking expenses

## Routing Logic

The router analyzes your question and activates relevant skills:

| Query Pattern | Activated Skills |
|--------------|------------------|
| "Find flights to [destination]" | flight_booking |
| "Book hotel in [city]" | hotel_reservation |
| "Plan [duration] trip to [destination]" | itinerary_generation |
| "Need travel insurance" | travel_insurance |
| "How much will trip cost?" | budget_tracking |
| "Plan complete Paris vacation" | ALL (coordinated) |

## Multi-Skill Coordination

Some requests require multiple skills working together:

### Complete Trip Planning
1. **budget_tracking** - Set budget constraints
2. **flight_booking** - Find flights within budget
3. **hotel_reservation** - Book accommodation
4. **itinerary_generation** - Create daily schedule
5. **travel_insurance** - Recommend coverage

### Booking Modification
1. **flight_booking** - Check flight change fees
2. **hotel_reservation** - Verify cancellation policy
3. **budget_tracking** - Calculate cost impact

## Usage Examples

**Simple (single skill):**
- "Find direct flights to Tokyo" → flight_booking
- "5-star hotels in Paris under $200/night" → hotel_reservation
- "Create 3-day Rome itinerary" → itinerary_generation

**Complex (multiple skills):**
- "Plan week-long Paris trip for 2, budget $3000" → budget_tracking → flight_booking → hotel_reservation → itinerary_generation
- "Cheapest way to visit London next month" → budget_tracking + flight_booking + hotel_reservation

## Quick Reference

### Flight Booking
- Search flights by route, dates, airline
- Compare prices across carriers
- Select seats, meals, baggage

### Hotel Reservation
- Filter by price, rating, amenities
- Check availability, reviews
- Book rooms with cancellation policy

### Itinerary Planning
- Generate day-by-day schedules
- Optimize routes between attractions
- Balance activities with free time

### Travel Insurance
- Compare coverage options
- Understand medical, cancellation policies
- File claims if needed

### Budget Tracking
- Estimate total trip cost
- Track expenses vs budget
- Optimize spending

## Working with This Skill

**Beginners:** Start with single-purpose queries ("Find flights to Paris")
**Intermediate:** Combine 2-3 aspects ("Find flights and hotel in Tokyo")
**Advanced:** Request complete trip planning with multiple constraints

The router handles complexity automatically - just ask naturally!
```

#### flight_booking.md（子技能）

```markdown
---
name: flight_booking
description: Flight search, booking, and airline comparisons
---

# Flight Booking

## When to Use This Skill

Use when searching for flights, comparing airlines, booking tickets, or managing flight reservations.

## Quick Reference

### Searching Flights

**Search by route:**
```
Find flights from [origin] to [destination]
Examples:
- "Flights from NYC to London"
- "JFK to Heathrow direct flights"
```

**Search with dates:**
```
Flights from [origin] to [destination] on [date]
Examples:
- "Flights from LAX to Paris on June 15"
- "Return flights NYC to Tokyo, depart May 1, return May 15"
```

**Filter by preferences:**
```
[direct/nonstop] flights from [origin] to [destination]
[airline] flights to [destination]
Cheapest/fastest flights to [destination]

Examples:
- "Direct flights from Boston to Dublin"
- "Delta flights to Seattle"
- "Cheapest flights to Miami next month"
```

### Booking Process

1. **Search** - Find flights matching criteria
2. **Compare** - Review prices, times, airlines
3. **Select** - Choose specific flight
4. **Customize** - Add seat, baggage, meals
5. **Confirm** - Book and receive confirmation

### Price Comparison

Compare across:
- Airlines (Delta, United, American, etc.)
- Booking sites (Expedia, Kayak, etc.)
- Direct vs connections
- Dates (flexible date search)
- Classes (Economy, Business, First)

### Seat Selection

Options:
- Window, aisle, middle
- Extra legroom
- Bulkhead, exit row
- Section preferences (front, middle, rear)

## Key Concepts

### Flight Types
- **Direct** - No stops, same plane
- **Nonstop** - Same as direct
- **Connecting** - One or more stops, change planes
- **Multi-city** - Different return city
- **Open-jaw** - Different origin/destination cities

### Fare Classes
- **Basic Economy** - Cheapest, most restrictions
- **Economy** - Standard coach
- **Premium Economy** - Extra space, amenities
- **Business** - Lie-flat seats, premium service
- **First Class** - Maximum luxury

### Booking Terms
- **Fare rules** - Cancellation, change policies
- **Baggage allowance** - Checked and carry-on limits
- **Layover** - Time between connecting flights
- **Codeshare** - Same flight, different airline numbers

## Working with This Skill

### For Beginners
Start with simple searches:
1. State origin and destination
2. Provide travel dates
3. Mention any preferences (direct, airline)

The skill will guide you through options step-by-step.

### For Intermediate Users
Provide more details upfront:
- Preferred airlines or alliances
- Class of service
- Maximum connections
- Price range
- Specific times of day

### For Advanced Users
Complex multi-city routing:
- Multiple destinations
- Open-jaw bookings
- Award ticket searches
- Specific aircraft types
- Detailed fare class codes

## Reference Files

All flight booking documentation is in `references/`:

- `flight_search.md` - Search strategies, filters
- `airline_policies.md` - Carrier-specific rules
- `booking_process.md` - Step-by-step booking
- `seat_selection.md` - Seating guides
- `fare_classes.md` - Ticket types, restrictions
- `baggage_rules.md` - Luggage policies
- `frequent_flyer.md` - Loyalty programs
```

---

## 实现指南

### 第 1 步：识别拆分点

**分析你的单体技能：**

1. 列出所有主要职责
2. 将相关功能分组
3. 识别自然边界
4. 计算每组行数

**示例：**

```
user_management.md (1800 lines)
├── Authentication (450 lines) ← Sub-skill
├── Profile CRUD (380 lines) ← Sub-skill
├── Permissions (320 lines) ← Sub-skill
├── Notifications (280 lines) ← Sub-skill
└── Activity logs (370 lines) ← Sub-skill
```

### 第 2 步：提取子技能

**对于每个识别出的组：**

1. 创建新的 `{subskill}.md` 文件
2. 复制相关内容
3. 添加适当的 frontmatter
4. 确保 200-500 行范围
5. 移除对其他组的依赖

**模板：**

```markdown
---
name: {subskill_name}
description: {clear, specific description}
---

# {Subskill Title}

## When to Use This Skill
[Specific use cases]

## Quick Reference
[Common operations]

## Key Concepts
[Domain terms]

## Working with This Skill
[Usage guidance by skill level]

## Reference Files
[Documentation structure]
```

### 第 3 步：创建路由器

**路由器技能模板：**

```markdown
---
name: {router_name}
description: {overall system description}
---

# {System Name} (Router)

## When to Use This Skill
{High-level description}

This is a router skill that directs queries to specialized sub-skills.

## Available Sub-Skills

### {subskill_1}
**Purpose:** {What it does}
**Keywords:** {routing, keywords, here}
**Use for:** {When to use}

### {subskill_2}
[Same pattern]

## Routing Logic

Based on query keywords:
- {keyword_group_1} → {subskill_1}
- {keyword_group_2} → {subskill_2}
- Multiple matches → Coordinate relevant skills

## Multi-Skill Operations

{Describe when multiple skills work together}

## Usage Examples

**Single skill:**
- "{example_query_1}" → {subskill_1}
- "{example_query_2}" → {subskill_2}

**Multiple skills:**
- "{complex_query}" → {subskill_1} + {subskill_2}
```

### 第 4 步：定义路由关键词

**最佳实践：**

- 每个子技能使用 5-10 个关键词
- 包含同义词和变体
- 要具体，不要通用
- 用真实查询测试

**示例：**

```markdown
### user_authentication
**Keywords:**
- Primary: login, logout, signin, signout, authenticate
- Secondary: password, credentials, session, token
- Variations: log-in, log-out, sign-in, sign-out
```

### 第 5 步：测试路由

**创建测试查询：**

```markdown
## Test Routing (Internal Notes)

Should route to user_authentication:
✓ "How do I log in?"
✓ "User login process"
✓ "Authentication failed"

Should route to user_profiles:
✓ "Update user profile"
✓ "Change profile picture"

Should route to multiple skills:
✓ "Create account and set up profile" → user_authentication + user_profiles
```

### 第 6 步：更新引用

**在每个子技能中：**

1. 链接到路由器以获取上下文
2. 引用相关的子技能
3. 更新导航路径

```markdown
## Related Skills

This skill is part of the {System Name} suite:
- **Router:** {router_name} - Main entry point
- **Related:** {related_subskill} - For {use case}
```

---

## 故障排除

### 路由器未正确激活子技能

**问题：** 查询路由到错误的子技能

**解决方案：**
1. 向路由器添加缺失的关键词
2. 使用更具体的路由关键词
3. 添加消除歧义的示例
4. 用查询措辞的变体测试

### 子技能过于细粒度

**问题：** 太多微小的子技能（每个 < 200 行）

**解决方案：**
- 合并相关的子技能
- 改为在单个技能中使用章节
- 每个子技能目标 300-500 行

### 子技能过大

**问题：** 子技能仍然超过 500 行

**解决方案：**
- 进一步拆分为更细粒度的关注点
- 考虑 3 层架构（路由器 → 类别路由器 → 特定技能）
- 将参考文档移到单独的文件

### 跨技能依赖

**问题：** 子技能经常需要彼此

**解决方案：**
1. 创建共享的参考文档
2. 使用路由器协调多技能操作
3. 重新考虑拆分边界（可能过于细粒度）

### 路由器逻辑过于复杂

**问题：** 路由器有大量条件逻辑

**解决方案：**
- 简化为基于关键词的路由
- 创建中间路由器（2 层）
- 记录显式的路由表

**2 层示例：**

```
main_router.md
├── user_features_router.md
│   ├── authentication.md
│   ├── profiles.md
│   └── permissions.md
└── admin_features_router.md
    ├── analytics.md
    ├── reporting.md
    └── configuration.md
```

---

## 适配自动生成的路由器

Skill Seeker 使用 `generate_router.py` 为大型文档自动生成路由器技能。

**你可以将其适配为手动技能：**

### 1. 研究模式

```bash
# 从文档配置生成路由器
python -m skill_seekers.cli.split_config configs/godot.json --strategy router
skill-seekers create configs/godot-*.json

# 检查生成的路由器 SKILL.md
cat output/godot/SKILL.md
```

### 2. 提取模板

生成的路由器包含：
- 子技能描述
- 基于关键词的路由
- 使用示例
- 多技能协调说明

### 3. 定制你的用例

将文档特定内容替换为你的应用逻辑：

```markdown
# Generated (documentation):
### godot-scripting
GDScript programming, signals, nodes
Keywords: gdscript, code, script, programming

# Customized (your app):
### order_processing
Process customer orders, payments, fulfillment
Keywords: order, purchase, payment, checkout, fulfillment
```

---

## 总结

### 关键要点

1. ✅ **500 行指南** 对最佳 Claude 性能很重要
2. ✅ **路由器模式** 可在保持限制的同时实现复杂应用
3. ✅ **单一职责** - 每个子技能做好一件事
4. ✅ **上下文效率** - 每个任务只加载所需内容
5. ✅ **经过验证的方法** - 已成功用于大型文档

### 何时应用此模式

**在以下情况使用技能分层：**
- 技能超过 500 行
- 多个不同的职责
- 不同部分很少一起使用
- 团队希望模块化维护

**在以下情况不使用技能分层：**
- 技能少于 500 行
- 单一、内聚的职责
- 所有内容经常一起使用
- 简洁性是优先事项

### 后续步骤

1. 审查现有技能，寻找拆分候选
2. 按照上述模板创建路由器 + 子技能
3. 用真实查询测试路由
4. 根据使用情况优化关键词
5. 迭代改进

---

## 其他资源

- **自动生成的路由器：** 请参阅 `docs/LARGE_DOCUMENTATION.md` 了解抓取文档的自动拆分
- **路由器实现：** 请参阅 `src/skill_seekers/cli/generate_router.py` 了解参考实现
- **示例：** 请参阅 `configs/` 中的配置了解真实的路由器模式

**有问题或反馈？** 在 GitHub 上打开一个 issue！
