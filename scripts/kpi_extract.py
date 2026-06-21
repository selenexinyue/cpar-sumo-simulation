#!/usr/bin/env python3
"""
KPI 提取脚本 (SPF 框架, Report 1.3节)
用法:
  1) 先跑仿真打开三个输出:
     sumo -c <option>.sumocfg \
       --device.ssm.probability 1 --device.ssm.measures "TTC DRAC" --device.ssm.file ssm_<opt>.xml \
       --device.emissions.probability 1 --tripinfo-output tripinfo_<opt>.xml
  2) 提取该 option 的 8 项原始 KPI:
     python3 kpi_extract.py ssm_<opt>.xml tripinfo_<opt>.xml <opt名>
  对 option1/2/3 各跑一次, 把结果填进 kpi_values 字典, 再跑 kpi_score() 出总分.
"""
import re, sys, json, statistics

def _is_smv(vid): return vid.lower().startswith('smv_')

def _count_conflicts(ssm_text, exclude_smv_main=True):
    """逐 conflict 块解析 ego/foe + minTTC/maxDRAC.
    exclude_smv_main=True 时剔除 SMV↔主路冲突(高架/隧道立体交叉,本不该算);
    保留 主路↔主路 与 SMV↔SMV(服务道内部真实平面冲突)."""
    ttc_n = drac_n = 0
    for b in re.split(r'<conflict ', ssm_text)[1:]:
        e = re.search(r'ego="([^"]+)"', b); f = re.search(r'foe="([^"]+)"', b)
        if not e or not f: continue
        es, fs = _is_smv(e.group(1)), _is_smv(f.group(1))
        is_smv_main = (es != fs)            # 恰好一方是 SMV -> SMV↔主路
        if exclude_smv_main and is_smv_main: continue
        mt = re.search(r'<minTTC [^>]*value="([\d.]+)"', b)
        md = re.search(r'<maxDRAC [^>]*value="([\d.]+)"', b)
        if mt and float(mt.group(1)) < 1.5: ttc_n += 1
        if md and float(md.group(1)) > 3.0: drac_n += 1
    return ttc_n, drac_n

def extract(ssm_file, tripinfo_file, label, exclude_smv_main=True):
    ssm = open(ssm_file).read()
    ttc_incidents, drac_incidents = _count_conflicts(ssm, exclude_smv_main)
    tinfo = open(tripinfo_file).read()
    # 逐条解析,把 departDelay(入口排队等待)纳入拥堵
    dur=[]; rl=[]; tl=[]; dd=[]
    for m in re.finditer(r'<tripinfo ([^>]*?)>', tinfo):
        a = m.group(1)
        def g(n):
            mm = re.search(n + r'="(-?[\d.]+)"', a); return float(mm.group(1)) if mm else 0.0
        dur.append(g('duration')); rl.append(g('routeLength')); tl.append(g('timeLoss')); dd.append(g('departDelay'))
    tt   = [dur[i] + dd[i] for i in range(len(dur))]   # 全程行程时间 = 网内 + 入口等待
    dly  = [tl[i]  + dd[i] for i in range(len(dur))]   # 全程延误     = 网内timeLoss + 入口等待
    co2 = sum(float(x) for x in re.findall(r'CO2_abs="([\d.]+)"', tinfo))/1e6
    nox = sum(float(x) for x in re.findall(r'NOx_abs="([\d.]+)"', tinfo))/1e6
    pm  = sum(float(x) for x in re.findall(r'PMx_abs="([\d.]+)"', tinfo))/1e6
    k = {
        'ttc_incidents':  ttc_incidents,   # 安全 20% 低好 (已剔除SMV↔主路)
        'drac_incidents': drac_incidents,  # 安全 20% 低好 (已剔除SMV↔主路)
        'avg_speed_ms':   sum(rl)/sum(tt),                   # 拥堵 10% 高好 (含入口等待的有效速度)
        'avg_delay_s':    statistics.mean(dly),              # 拥堵 10% 低好 (含 departDelay)
        'p95_tt_s':       sorted(tt)[int(0.95*len(tt))],     # 拥堵 10% 低好 (含 departDelay)
        'co2_kg':         co2,                               # 排放 10% 低好
        'nox_kg':         nox,                               # 排放 10% 低好
        'pm_kg':          pm,                                # 排放 10% 低好
        '_completed':     len(dur),
    }
    print(f"[{label}] " + json.dumps(k, indent=2, ensure_ascii=False))
    return k

# 权重 + 方向 ('-'=低好, '+'=高好)
WEIGHTS = {'ttc_incidents':(0.20,'-'),'drac_incidents':(0.20,'-'),
           'avg_speed_ms':(0.10,'+'),'avg_delay_s':(0.10,'-'),'p95_tt_s':(0.10,'-'),
           'co2_kg':(0.10,'-'),'nox_kg':(0.10,'-'),'pm_kg':(0.10,'-')}

def kpi_score(values):  # values = {'option1':{...}, 'option2':{...}, 'option3':{...}}
    opts = list(values)
    out = {o:0.0 for o in opts}
    norm_table = {}
    for m,(w,d) in WEIGHTS.items():
        col = {o: values[o][m] for o in opts}
        lo, hi = min(col.values()), max(col.values())
        norm = {}
        for o in opts:
            if hi == lo: norm[o] = 100.0
            elif d == '-': norm[o] = 100*(hi - col[o])/(hi - lo)   # 低好
            else:          norm[o] = 100*(col[o] - lo)/(hi - lo)   # 高好
            out[o] += w * norm[o]
        norm_table[m] = norm
    print("\n=== 归一化后各指标得分 (0-100) ===")
    print("指标".ljust(18) + "".join(o.ljust(12) for o in opts))
    for m in WEIGHTS:
        print(m.ljust(18) + "".join(f"{norm_table[m][o]:.1f}".ljust(12) for o in opts))
    print("\n=== SPF 总分 (越高越优) ===")
    for o in sorted(out, key=out.get, reverse=True):
        print(f"  {o}: {out[o]:.1f}")
    return out

if __name__ == '__main__':
    if len(sys.argv) >= 4:
        extract(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
