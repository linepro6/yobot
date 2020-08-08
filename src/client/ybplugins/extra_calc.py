import re
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

UNIT_DICT = {
    'W': 10000,
    'w': 10000,
    '万': 10000,
    'k': 1000,
    'K': 1000,
    '千': 1000,
}

def extra_time_cal(match):
    if not match:
        return None
    units = []
    for i in [2, 4, 6]:
        units.append(UNIT_DICT.get(match.group(i), 1))

    numbers = []
    for x in range(3):
        numbers.append((int(match.group(2 * x + 1)) * units[x], match.group(
            2 * x + 1) + ("" if not match.group(2 * x + 2) else match.group(2 * x + 2))))

    # numbers = sorted(numbers, key=lambda x: x[0])

    boss = numbers[0][0]
    pred_A = numbers[1][0]
    pred_B = numbers[2][0]
    pred_A_str = numbers[1][1]
    pred_B_str = numbers[2][1]

    if pred_A > boss:
        return "{} 的刀已经将 BOSS 击败。".format(pred_A_str)
    
    if pred_A + pred_B < boss:
        return "两刀不能将 BOSS 击杀。"
    

    pred_time = 100 - 90 * (boss - pred_A) / pred_B
    if pred_time > 90:
        pred_time = 90
    else:
        pred_time = int(pred_time) + \
            1 if pred_time > int(pred_time) else int(pred_time)

    msg = """1. 先出 {} 的刀，再出 {} 的刀。
2. 后者可以获得补偿时间：{} 秒。""".format(pred_A_str, pred_B_str, pred_time)
    return msg

def damage_cal(match):
    if not match:
        return None
    units = []
    for i in [2, 4]:
        units.append(UNIT_DICT.get(match.group(i), 1))
    boss = int(match.group(1)) * units[0]
    pred_A = int(match.group(3)) * units[1]

    if boss < pred_A:
        t = boss
        boss = pred_A
        pred_A = t

    damage = (boss - pred_A) * (90 / 10.999999999999)
    result = damage + 1

    if damage > 10000:
        result = damage / 10000
        result = int(result) + 1 if result > int(result) else result
        result = str(result) + " 万"
    msg = "合刀中另一刀获得补时 90 秒所需的最低伤害为：{}。".format(result)
    if boss < damage:
        pred_time = 100 - 90 * (boss - pred_A) / boss
        if pred_time > 90:
            pred_time = 90
        else:
            pred_time = int(pred_time) + \
                1 if pred_time > int(pred_time) else pred_time
        msg = msg + "\n如果另一刀将 BOSS 击杀则可获得补时 {} 秒。".format(pred_time)
    return msg

class ExtraCalc:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):
        return

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        cmd = ctx['raw_message']
        match = re.match(r'^补时计算 *(\d+)([Ww万Kk千])? +(\d+)([Ww万Kk千])? +(\d+)([Ww万Kk千])? *$', cmd)
        if not match:
            match = re.match(r'^合刀查找 *(\d+)([Ww万Kk千])? +(\d+)([Ww万Kk千])? *$', cmd)
            if not match:
                return
            else: return damage_cal(match)
        else: return extra_time_cal(match)
