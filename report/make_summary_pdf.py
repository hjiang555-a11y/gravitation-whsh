# -*- coding: utf-8 -*-
"""武汉—上海远程光钟比对实验 总结报告 PDF（一页一大图，图内文字可读）"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image
import matplotlib.image as mpimg

zh = fm.FontProperties(fname='/usr/share/fonts/truetype/wqy/wqy-microhei.ttc')
plt.rcParams['axes.unicode_minus'] = False

DARKBLUE = '#1F497D'; NAVY = '#2D2D8A'; RED = '#C0504D'
GREEN = '#4E8A3D'; GRAY = '#595959'

FIGW, FIGH = 11.69, 8.27   # A4 横向英寸
PRJ = '/home/room115/gravitation-whsh/'

# 一页一大图：图按"可用宽 270mm / 可用高 165mm"等比缩放
MAXW, MAXH = 270/25.4, 165/25.4   # 英寸

def place_pic(fig, path, caption):
    im = Image.open(PRJ + path); w, h = im.size
    scale = min(MAXW/w, MAXH/h)
    disp_w, disp_h = w*scale, h*scale  # 英寸
    # 居中放置
    x = (FIGW - disp_w)/2
    y = 1.0 + (FIGH - 2.2 - disp_h)/2  # 标题栏~1.0英寸高, 图题~0.4英寸
    ax = fig.add_axes([x/FIGW, y/FIGH, disp_w/FIGW, disp_h/FIGH])
    ax.imshow(mpimg.imread(PRJ+path)); ax.axis('off')
    # 图题放图上方
    if caption:
        fig.text(0.5, (y+disp_h+0.12)/FIGH, caption, fontsize=12, ha='center',
                 color=DARKBLUE, fontproperties=zh)

def bar(fig, text):
    ax = fig.add_axes([0, (FIGH-0.75)/FIGH, 1, 0.75/FIGH])
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
    ax.add_patch(plt.Rectangle((0,0),1,1,color=DARKBLUE,transform=ax.transAxes))
    ax.text(0.03, 0.5, text, transform=ax.transAxes, fontsize=16, fontweight='bold',
            color='white', va='center', fontproperties=zh)

def figpage():
    fig = plt.figure(figsize=(FIGW, FIGH))
    return fig

# 关键图列表（一页一张）
FIGS = [
    ('report/fig1_timeseries_7d.png', '前 7 天五分量时域：固体潮(生成/诱导/有效) + 海潮负荷 + 总势差'),
    ('report/fig2_spectrum.png', '潮汐势差频谱（M2/S2/N2/K1/O1/P1 谱线）'),
    ('report/fig3_full_68d.png', '68 天总潮汐势差全程 + 日 min–max 包络 + 日平均'),
    ('report/fig4_frequency_shift.png', '钟频差 Δf/f = ΔW/c²（引力红移），峰峰值 ~1.6e-17'),
    ('clock/segment_analysis/batch_forest.png', '14 段幅度比 A ± u_A（森林图）：12/14 段为负'),
    ('clock/segment_analysis/batch_shared_axis.png', '逐段拍频 vs 潮汐模板（1200-s 三角窗）'),
    ('clock/correlation.png', '14 组会话宏观正相关：Pearson r = +0.472'),
    ('clock/clock_tidal_shift.png', '14 组会话平均潮汐频差 Δf/f（×1e-18）'),
    ('clock/temperature/temperature_diurnal.png', '三站气温日周期轮廓（上海/武汉/合肥）'),
    ('clock/temperature/fx_b2_lock_fraction.png', '环外 10MHz 信号(FXE_B2)逐日锁定比例'),
    ('clock/temperature/fx_b4_vs_temperature.png', '超稳参考 FXE_B4 vs 温度（无耦合）'),
    ('clock/session_dff_old_vs_professional.png', '旧(HARPOS) vs 专业 海潮负荷会话潮汐频差'),
    ('clock/comparison_scatter.png', '旧 vs 专业 海潮负荷会话频差散点（corr≈0.91）'),
]

with PdfPages('/tmp/opencode/ppt_build/final_big.pdf') as pdf:
    # 封面
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); ax.axis('off')
    ax.text(0.5, 0.62, '武汉—上海远程光钟比对实验', fontsize=30, fontweight='bold',
            color=DARKBLUE, ha='center', fontproperties=zh)
    ax.text(0.5, 0.52, '引力潮汐引力红移效应分析 · 总结报告', fontsize=16, color=NAVY, ha='center', fontproperties=zh)
    ax.text(0.5, 0.44, '潮汐势差计算 · 光纤链路 · 实验数据处理', fontsize=12, color=GRAY, ha='center', fontproperties=zh)
    ax.text(0.5, 0.28, '2026 年 6 月—8 月 · 14 段无跳点实验\n1550 nm 传递链路（武汉 → 合肥 → 上海）',
            fontsize=11, color=GRAY, ha='center', fontproperties=zh, linespacing=1.8)
    pdf.savefig(fig); plt.close(fig)

    # 一页一大图
    for path, cap in FIGS:
        fig = figpage()
        bar(fig, cap.split('：')[0] if '：' in cap else cap)
        place_pic(fig, path, cap)
        pdf.savefig(fig); plt.close(fig)

    # 结论页
    fig = figpage()
    bar(fig, '结论')
    fig.text(0.08, 0.10, 
        '1. 潮汐引力红移被检出：段级 12/14 负相关，|z|=6.33（p=2.5e-10），A=−0.52±0.08（6.8σ）\n\n'
        '2. 会话级宏观正相关 r=+0.472（10/14 同号）— 与理论方向一致、更鲁棒\n\n'
        '3. 海潮负荷修正 3.9 倍（专业序列），固体潮波形完全一致\n\n'
        '4. 噪声本底 = 钟白频率噪声(1/√τ)，链路白相位(1/τ) 不影响潮汐检测\n\n'
        '5. 温度影响不可检出，不改变潮汐结论',
        fontsize=15, va='top', fontproperties=zh, color='#222', linespacing=2.0)
    pdf.savefig(fig); plt.close(fig)

    # 建议页
    fig = figpage()
    bar(fig, '建议：如何提升检测力与产出的方向')
    fig.text(0.08, 0.10,
        '1. 定死 s_beat 符号（梳尺/本振频率高低）— 0 成本，确定潮汐物理方向\n\n'
        '2. 两钟直接比对代替 1550nm 传递链路拍频 — 去掉链路白相位噪声、降本底\n\n'
        '3. 增加独立实验段数 N（u_A ∝ 1/√N）：~33段→10%，~133段→5%，~368段→3%\n\n'
        '4. 采集链路双向时延 / 机架温度日志 — 量化温度-链路耦合\n\n'
        '5. 确认高程差项 u_H（PDF标注待定）与潮汐 ΔW 同量级，显式核算避免混淆',
        fontsize=15, va='top', fontproperties=zh, color='#222', linespacing=2.0)
    pdf.savefig(fig); plt.close(fig)

print("saved final_big.pdf")
