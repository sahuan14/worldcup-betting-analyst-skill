# worldcup-betting-analyst

世界杯竞彩足球 · 诚实分析助手 — 一个 [Claude Code](https://claude.com/claude-code) Skill。

在世界杯及赛前热身赛期间，帮你对**中国竞彩足球**做有依据的分析与推荐。覆盖胜平负、让球胜平负、比分、总进球、半全场、串关全部玩法。

## 这个 Skill 能做什么

- 自动从体彩官网 API（sporttery.cn）抓取实时竞彩赔率和单关/过关状态
- 结合网络搜索获取两队近况、伤停、首发、战意等信息
- 对每场比赛给出完整分析卡片 + 明确的购票推荐（含星级评价）
- 多场分析时自动给出串关建议和总结表
- 主动识别情绪化陷阱（追注、凑串、押低赔热门），善意提醒

## 核心原则

**这个 Skill 不能让你赚钱。** 竞彩抽水约 27%，长期净赚对任何人都几乎不可能。它只帮你：
1. 每一注都有依据，不拍脑袋
2. 避开最烂的坑（乱串关、压死赔率的热门、为凑串塞弱场）
3. 知道什么时候该跳过

把足彩当花得明白的娱乐，这个 Skill 就值。

## 安装

将 `SKILL.md` 放到 Claude Code 的 skills 目录中：

**个人级别（所有项目可用）：**
```bash
mkdir -p ~/.claude/skills/worldcup-betting-analyst
cp SKILL.md ~/.claude/skills/worldcup-betting-analyst/
```

**项目级别（仅当前项目可用）：**
```bash
mkdir -p .claude/skills/worldcup-betting-analyst
cp SKILL.md .claude/skills/worldcup-betting-analyst/
```

安装后在 Claude Code 中输入 `/worldcup-betting-analyst` 即可调用，或者直接聊天提到世界杯、竞彩、买球等关键词时会自动触发。

## 使用示例

```
> 今晚有什么值得买的？
> 帮我看看法国vs科特迪瓦怎么买
> 西班牙这场让3球合理吗？
> 今晚几场比赛帮我串一个
```

完整的输出示例见 [examples/sample-output.md](examples/sample-output.md)。

## 数据来源

| 数据 | 来源 |
|---|---|
| 竞彩赔率 + 单关状态 | 体彩官网 JSON API（sporttery.cn） |
| 球队近况 / 伤停 / 首发 | 网络搜索（实时获取） |
| 国外赔率（对照用） | 网络搜索（实时获取） |

> **注意：** 主数据源 sporttery.cn 为中国体彩官网，需在国内网络环境下使用。API 为非官方公开接口，可能随官网改版变动。

## 环境要求

- [Claude Code](https://claude.com/claude-code)
- 国内网络环境（用于访问体彩官网 API）

## 许可证

[MIT License](LICENSE)
