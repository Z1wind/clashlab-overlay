# -*- coding: utf-8 -*-
"""生成 knowledge/strategies.json 与 knowledge/hero_equipment.json（schema 对齐契约测试）。"""
import json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
KN = os.path.join(BASE, "knowledge")
os.makedirs(KN, exist_ok=True)

def troops(**kw):
    return {k.replace("_", "-"): int(v) for k, v in kw.items()}

def by_th(base, scale):
    out = {}
    for th in range(13, 20):
        out[str(th)] = {k: max(1, int(round(v * (scale + 0.02 * (th - 13))))) for k, v in base.items()}
    return out

S = []
def add(sid, arch, name, base, steps, queries, tags, why, conf, src="community-meta"):
    S.append({"id": sid, "archetype": arch, "name": name,
              "troops_by_th": by_th(base, 1.0),
              "weakness_tags": tags, "why": why,
              "steps": steps, "video_queries": queries,
              "source": src, "confidence": conf})

add("air-edrag", "air", "电龙平推（Air spam）",
    troops(electro_dragon=7, balloon=12, rage=3, freeze=2),
    ["外围清边，逼出空气炮", "电龙沿逆风侧一字排开", "狂暴+冰冻强拆核心防空", "英雄收尾清外围"],
    ["TH16 electro dragon attack strategy", "clash of clans air army 3 star"],
    ["air-gap"], "对空覆盖不足时，空中单位可以越过墙体直取核心。", 0.72)

add("air-lavaloon", "air", "熔岩猎犬 + 气球（LaLoon）",
    troops(lava_hound=3, balloon=24, rage=3, haste=2),
    ["猎犬先手打掉一处防空", "气球分两路压剩余防空", "狂暴推进核心", "冰冻给单头地狱塔"],
    ["TH16 lavaloon strategy", "clash of clans lava hound balloon 3 star"],
    ["air-gap"], "猎犬吸防空火力，气球快速点名核心防御。", 0.68)

add("air-dragon", "air", "飞龙平推（Dragon spam）",
    troops(dragon=10, balloon=8, rage=3, freeze=1),
    ["一侧清边", "飞龙一字排开", "狂暴集中破防空", "冰冻收尾"],
    ["clash of clans dragon attack strategy", "TH16 dragon spam"],
    ["air-gap"], "防空分散且级别低时，飞龙群可以平推。", 0.6)

add("ground-smash-yeti", "ground", "雪怪女巫强拆（Smash）",
    troops(yeti=4, witch=6, golem=2, bowler=8, jump=2, rage=2),
    ["双雪怪开墙", "炸弹人破第一层后下主力", "跳墙直插核心", "女巫骷髅掩护侧翼"],
    ["TH16 yeti smash attack", "clash of clans witch golem smash"],
    ["compartment-density"], "隔间密集或墙效率低时，跳墙+雪怪能一波推平核心。", 0.7)

add("ground-pekka", "ground", "皮卡超人强拆（Pekka smash）",
    troops(pekka=4, wizard=8, bowler=6, jump=2, rage=2),
    ["清边建立推进走廊", "皮卡带狂暴进核心", "跳墙越过第二层", "法师补伤害"],
    ["TH16 pekka smash", "clash of clans pekka attack"],
    ["compartment-density"], "墙多、隔间深时，皮卡+跳墙可以一路砍穿。", 0.66)

add("ground-hog", "ground", "野猪骑士 + 治愈（Hog rush）",
    troops(hog_rider=30, heal=4, rage=1, freeze=1),
    ["先点掉炸弹塔区域", "野猪扇形展开", "治疗覆盖爆炸陷阱", "英雄收尾清边"],
    ["TH16 hog rider attack", "clash of clans hog rush"],
    ["th-bias"], "外侧防御暴露、大本营偏心时，野猪可以成扇形点名。", 0.64)

add("hero-dive-queen", "hero-dive", "女王切入（Queen charge）",
    troops(healer=4, wall_breaker=6, miner=12, rage=2, freeze=1),
    ["女王+天使从弱点侧开墙", "狂暴压核心防御", "矿工从缺口进入", "冰冻保护女王"],
    ["TH16 queen charge attack", "clash of clans queen walk"],
    ["th-bias"], "大本营偏心时，用女王从弱点侧直接拆核心。", 0.75)

add("hero-dive-blimp", "hero-dive", "飞艇偷核心（Blimp snipe）",
    troops(balloon=18, clone=2, rage=2, haste=1),
    ["先清一侧防空", "飞艇直飞核心", "克隆+狂暴砸核心", "后续气球补刀"],
    ["TH16 blimp attack", "clash of clans blimp strategy"],
    ["th-bias"], "核心区防空被吸引后，飞艇+克隆可以砸穿大本营区域。", 0.71)

add("hybrid-miner", "hybrid", "矿工 + 女王混编（Hybrid）",
    troops(miner=20, hog_rider=10, healer=4, heal=3, rage=2),
    ["女王先切一侧", "矿工从缺口进入", "治疗覆盖陷阱", "野猪补核心"],
    ["TH16 hybrid attack", "clash of clans miner hog hybrid"],
    ["general"], "没有单一明显弱点时，混合路线更稳。", 0.69)

add("hybrid-bowler", "hybrid", "投石手 + 女王（Bowler hybrid）",
    troops(bowler=10, healer=4, miner=12, jump=1, rage=2),
    ["投石手清边", "女王切入", "跳墙进核心", "矿工补刀"],
    ["TH16 bowler attack", "clash of clans bowler hybrid"],
    ["general"], "远程溅射压制 + 女王切入，适合均衡阵型。", 0.63)

add("ground-root-rider", "ground", "根蔓骑士突进（Root Rider）",
    troops(root_rider=6, valkyrie=8, heal=3, rage=2),
    ["根蔓骑士打头阵", "女武神跟进清边", "治疗覆盖核心", "英雄补刀"],
    ["TH16 root rider attack", "clash of clans root rider"],
    ["compartment-density"], "根蔓骑士无视墙体，适合墙厚但隔间差的阵型。", 0.58, src="community-meta(low)")

add("general-balanced", "hybrid", "通用均衡模板",
    troops(giant=12, wizard=10, archer=20, heal=2, rage=1),
    ["坦克开路", "远程跟进", "治疗覆盖核心", "英雄收尾"],
    ["clash of clans attack basics guide"],
    ["general"], "缺少明显弱点数据时的保守模板：坦克开路 + 远程输出。", 0.5, src="baseline")

data = {"version": 2, "updated_at": "2026-11-26",
        "note": "社区 meta 参考模板，非官方数据；视频只给搜索入口，不存储第三方内容。",
        "strategies": S}
json.dump(data, open(os.path.join(KN, "strategies.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

eq = {"version": 2, "updated_at": "2026-11-26",
      "disclaimer": "以下为参考建议，非官方数据；请结合版本与个人习惯调整。",
      "recommendations": {
          "13": {"queen": {"equipment": ["giant-arrow", "healer-puppet"], "tips": ["巨人箭拆多层墙"]},
                 "king": {"equipment": ["earthquake-boots", "vampstache"], "tips": ["地震靴开墙"]}},
          "14": {"queen": {"equipment": ["giant-arrow", "invisibility-vial"], "tips": ["隐身保护切入"]},
                 "king": {"equipment": ["earthquake-boots", "rage-vial"], "tips": ["狂暴补输出"]}},
          "15": {"queen": {"equipment": ["giant-arrow", "healer-puppet"], "tips": ["治疗木偶续航"]},
                 "warden": {"equipment": ["eternal-tome", "life-gem"], "tips": ["大招覆盖核心"]}},
          "16": {"queen": {"equipment": ["giant-arrow", "healer-puppet"], "tips": ["巨人箭+治疗切入"]},
                 "king": {"equipment": ["earthquake-boots", "vampstache"], "tips": ["坦克流带吸血"]},
                 "warden": {"equipment": ["eternal-tome", "life-gem"], "tips": ["保核心推进"]},
                 "royal-champion": {"equipment": ["royal-gem", "seeking-shield"], "tips": ["收尾清边"]}},
          "17": {"queen": {"equipment": ["giant-arrow", "invisibility-vial"], "tips": ["高本核心更硬，带隐身"]},
                 "king": {"equipment": ["earthquake-boots", "rage-vial"], "tips": ["强拆开墙"]},
                 "warden": {"equipment": ["eternal-tome", "life-gem"], "tips": ["大范围覆盖"]},
                 "royal-champion": {"equipment": ["royal-gem", "seeking-shield"], "tips": ["远程投掷"]}},
          "18": {"queen": {"equipment": ["giant-arrow", "healer-puppet"], "tips": ["续航优先"]},
                 "king": {"equipment": ["earthquake-boots", "vampstache"], "tips": ["吸血保坦"]},
                 "warden": {"equipment": ["eternal-tome", "life-gem"], "tips": ["核心推进"]},
                 "royal-champion": {"equipment": ["royal-gem", "seeking-shield"], "tips": ["清边收尾"]}},
          "19": {"queen": {"equipment": ["giant-arrow", "invisibility-vial"], "tips": ["高本护盾多，带隐身"]},
                 "king": {"equipment": ["earthquake-boots", "rage-vial"], "tips": ["开墙+狂暴"]},
                 "warden": {"equipment": ["eternal-tome", "life-gem"], "tips": ["覆盖全队"]},
                 "royal-champion": {"equipment": ["royal-gem", "seeking-shield"], "tips": ["远程补刀"]}}
      }}
json.dump(eq, open(os.path.join(KN, "hero_equipment.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("strategies:", len(S), "| hero TH keys:", sorted((eq["recommendations"]).keys()))
