# worldcup-betting-analyst

世界杯竞彩足球 · 诚实分析助手。这个 skill 可用于 Claude Code 和 Codex，帮助用户在世界杯及赛前热身赛期间分析中国竞彩足球玩法。

它的目标不是“保证命中”，而是：

1. 把实时赔率、单关/过关状态、伤停、首发、战意和市场概率查清楚。
2. 用比赛原型分析强弱对位、破密集防守、小组赛算分、同级缠斗等关键问题。
3. 明确区分“看好赛果”“相对可买”和“赔率是否真的有价值”。
4. 用主推、可选、博取、跳过做分层推荐，而不是非黑即白。
5. 识别低赔热门、乱串关、追注、借钱下注等高风险行为。

## 能做什么

- 从体彩官网 API 抓取竞彩赔率和单关/过关状态。
- 结合实时搜索分析近况、伤停、首发、战意、世界杯/大赛履历。
- 用低抽水市场概率做校准，避免纯靠主观判断。
- 输出单场分析卡片、分层推荐、串关建议和总结表。
- 在信息不足或赔率无价值时降级推荐强度；没有清晰方向时才建议跳过。

## 文件结构

```text
worldcup-betting-analyst/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── fetch_sporttery.py
│   └── odds_math.py
└── examples/
    └── sample-output.md
```

## 安装到 Codex

个人级别：

```bash
mkdir -p ~/.agents/skills/worldcup-betting-analyst
cp -R SKILL.md agents scripts examples ~/.agents/skills/worldcup-betting-analyst/
```

项目级别：

```bash
mkdir -p .agents/skills/worldcup-betting-analyst
cp -R SKILL.md agents scripts examples .agents/skills/worldcup-betting-analyst/
```

在 Codex 中可以显式输入：

```text
$worldcup-betting-analyst 帮我看看今晚世界杯竞彩怎么买
```

也可以直接提到世界杯、竞彩、足彩、买球、串关等关键词，让 Codex 自动判断是否触发。

## 安装到 Claude Code

个人级别：

```bash
mkdir -p ~/.claude/skills/worldcup-betting-analyst
cp -R SKILL.md scripts examples ~/.claude/skills/worldcup-betting-analyst/
```

项目级别：

```bash
mkdir -p .claude/skills/worldcup-betting-analyst
cp -R SKILL.md scripts examples .claude/skills/worldcup-betting-analyst/
```

在 Claude Code 中可以显式调用：

```text
/worldcup-betting-analyst
```

或直接用自然语言提问。

## 辅助脚本

抓取体彩赔率：

```bash
python3 scripts/fetch_sporttery.py --pretty
```

如果你在可信的本地代理环境里遇到自签证书错误，可以显式加：

```bash
python3 scripts/fetch_sporttery.py --pretty --insecure
```

计算赔率隐含概率、去水概率和粗略 EV：

```bash
python3 scripts/odds_math.py --odds 1.80 3.40 4.20 --my-probs 0.55 0.27 0.18 --pretty
```

脚本只使用 Python 标准库，便于在 Claude Code、Codex 和普通终端里运行。

`fetch_sporttery.py` 会把单个玩法请求失败记录到 `errors`，并继续输出其他成功玩法的数据，避免一个临时接口问题卡住整场分析。

脚本会根据中国竞彩网“竞彩销售时间”计算 `computed_times.computed_cutoff`：

```text
周一至周五 11:00-22:00
周六、周日 11:00-23:00
截售 = min(比赛开赛时间, 销售日官方停售时间)
```

## 数据来源

| 数据 | 来源 |
|---|---|
| 竞彩赔率 + 单关状态 | 体彩官网 JSON API |
| 近况 / 伤停 / 首发 / 战意 | 实时网络搜索和权威媒体 |
| 国外低抽水盘 | 实时网络搜索或可用赔率源 |

主数据源 `sporttery.cn` 需要可访问国内体彩官网 API。若当前环境禁网或域名未放行，skill 会要求明确告知用户，不凭记忆补数据。

## 使用示例

```text
> 今晚有什么值得买的？
> 帮我看看法国 vs 科特迪瓦怎么买
> 西班牙让 3 球合理吗？
> 小组赛最后一轮这几场帮我串一个
```

这里的“今晚”按中国竞彩语境理解为当天晚间到第二天上午的在售比赛，不只限于日历当天或凌晨前。

完整输出示例见 [examples/sample-output.md](examples/sample-output.md)。

## 许可证

[MIT License](LICENSE)
