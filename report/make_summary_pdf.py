# -*- coding: utf-8 -*-
"""武汉—上海远程光钟比对实验 总结报告 PDF 生成（matplotlib 逐页精确排版）"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from PIL import Image

# 中文字体
zh = fm.FontProperties(fname='/usr/share/fonts/truetype/wqy/wqy-microhei.ttc')
plt.rcParams['axes.unicode_minus'] = False

DARKBLUE = '#1F497D'
NAVY = '#2D2D8A'
RED = '#C0504D'
GREEN = '#4E8A3D'
GRAY = '#595959'
LIGHT = '#EEECE1'

FIGW, FIGH = 11.69, 8.27  # A4 横向英寸
PRJ = '/home/room115/gravitation-whsh/'

def figpage():
    fig = plt.figure(figsize=(FIGW, FIGH))
    return fig

def title_bar(ax, text):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.add_patch(plt.Rectangle((0, 0.90), 1, 0.10, color=DARKBLUE, transform=ax.transAxes))
    ax.text(0.03, 0.945, text, transform=ax.transAxes, fontsize=17, fontweight='bold',
            color='white', va='center', fontproperties=zh)

def place_img(ax, path, x, y, w, text=None):
    """在 axes 坐标 (0-1) 放置图，按 w(宽度比例) 等比缩放；可选标题"""
    im = Image.open(PRJ + path)
    ar = im.size[0] / im.size[1]  # 宽/高
    h = w / ar  # 显示高度(以axes坐标=高度范围/宽度范围需换算)
    # 用 fig 坐标插图片更稳：fig.add_axes
    ax.imshow(im)
    ax.axis('off')
    ax.set_position([x, y, w, h])  # [left,bottom,width,height] 相对 figure
    if text:
        ax.text(0.5, -0.06, text, transform=ax.transAxes, fontsize=9,
                ha='center', color=GRAY, fontproperties=zh)

def text_block(fig, x, y, lines, size=10.5, color='#222222'):
    """在 figure 坐标放置文字块"""
    txt = fig.text(x, y, lines, fontsize=size, color=color, va='top', fontproperties=zh, linespacing=1.6)

colors = {
    'blue': DARKBLUE, 'red': RED, 'green': GREEN, 'gray': GRAY, 'navy': NAVY
}

with PdfPages('/tmp/opencode/ppt_build/summary2.pdf') as pdf:
    # ===== 第1页 封面 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); ax.axis('off'); ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.text(0.5, 0.62, '武汉—上海远程光钟比对实验', fontsize=30, fontweight='bold',
            color=DARKBLUE, ha='center', fontproperties=zh)
    ax.text(0.5, 0.52, '引力潮汐引力红移效应分析 · 总结报告', fontsize=16, color=NAVY, ha='center', fontproperties=zh)
    ax.text(0.5, 0.44, '潮汐势差计算 · 光纤链路 · 实验数据处理', fontsize=12, color=GRAY, ha='center', fontproperties=zh)
    ax.text(0.5, 0.28, '2026 年 6 月—8 月 · 14 段无跳点实验\n1550 nm 传递链路（武汉 → 合肥 → 上海）',
            fontsize=11, color=GRAY, ha='center', va='top', fontproperties=zh, linespacing=1.8)
    pdf.savefig(fig); plt.close(fig)

    # ===== 第2页 背景 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '项目背景：远程光钟比对 + 潮汐引力红移')
    text_block(fig, 0.04, 0.78,
        '• 两站光学原子钟：Yb（武汉 WUHN）vs Sr（上海 SHAO），经 1550nm 光纤链路远程比对\n'
        '• 潮汐周期改变两地重力势 ΔW，经引力红移 Δf/f = ΔW/c² 改变钟频差\n'
        '• ΔW/c² ≈ 4.8×10⁻¹⁸，恰在光学钟分辨能力边缘 —— 用真实原子钟验证潮汐引力红移\n'
        '• 难点：信号被噪声淹没约 3.6 倍，单段不显著，必须跨段统计合并', size=11)
    # 左：温度图 右：参数表
    axL = fig.add_axes([0,0,1,1]); place_img(axL, 'clock/temperature/temperature_diurnal.png', 0.04, 0.28, 0.46, '三站气温日周期轮廓 — 天周期温度影响不可检出')
    # 右侧参数
    text_block(fig, 0.56, 0.62,
        '关键参数\n\n'
        '链路拓扑      武汉→合肥→上海\n'
        '实验轮次      6月+8月，14段无跳点\n'
        '链路噪声      白相位 (σ∝1/τ)\n'
        '钟噪声        白频率 (σ∝1/√τ)\n'
        'COEF          4.282e-15\n'
        'delta_g       −3.116e-15', size=10.5)
    pdf.savefig(fig); plt.close(fig)

    # ===== 第3页 潮汐势差计算 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '引力潮汐：潮汐引力势差 ΔW 计算')
    ps = [
        ('report/fig1_timeseries_7d.png', 0.02, 0.48, 0.30, '前7天五分量时域'),
        ('report/fig2_spectrum.png', 0.34, 0.48, 0.64, '频谱（M2/S2/K1/O1 谱线）'),
        ('report/fig3_full_68d.png', 0.02, 0.13, 0.48, '68天全程+日包络'),
        ('report/fig4_frequency_shift.png', 0.34, 0.13, 0.64, '钟频差 Δf/f = ΔW/c²'),
    ]
    for path, x, y, w, cap in ps:
        im = Image.open(PRJ+path); ar = im.size[0]/im.size[1]
        h = w / ar  # 相对fig的高度(fig宽高比11.69/8.27)
        h = h * (FIGW/FIGH)  # 换算因为 axes 用figure坐标,y也是等比
        # 实际: set_position 的 width,height 都是相对 figure 的. 显示高度 = w * (fig宽/图宽比)
        # 简化: 用 fig.image 直接放
        import matplotlib.image as mpimg
        img = mpimg.imread(PRJ+path)
        ax2 = fig.add_axes([x, y, w, w/ar*(FIGW/FIGH)])
        ax2.imshow(img); ax2.axis('off')
        ax2.text(0.5, -0.05, cap, transform=ax2.transAxes, fontsize=9, ha='center', color=GRAY, fontproperties=zh)
    text_block(fig, 0.04, 0.055, '68 天完整序列：总潮汐势差 std = 0.371 m²/s²，峰值 −1.033（07-14）', size=11)
    pdf.savefig(fig); plt.close(fig)

    # ===== 第4页 海潮修正 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '专业海潮负荷数据修正（幅度 ~3.9×）')
    text_block(fig, 0.04, 0.76,
        '• 固体潮：波形 corr=1.0000，幅度 −5.2%（IERS Love 数更完整，非错误）\n'
        '• 海潮负荷：HARPOS FES2014b 偏低约 3.9×（SHAO M₂ ~8mm vs 专业 ~30mm）\n'
        '• 修正：--professional-ocean 用专业 30s 序列替换并固化\n'
        '• 修正后综合差与专业数据 corr = +0.9997', size=11)
    for path,x,y,w,cap in [
        ('clock/session_dff_old_vs_professional.png',0.04,0.28,0.46,'旧(HARPOS) vs 新(专业) 会话潮汐频差'),
        ('clock/comparison_scatter.png',0.52,0.28,0.44,'旧 vs 新散点（corr≈0.91 方向一致）'),
    ]:
        im=Image.open(PRJ+path); ar=im.size[0]/im.size[1]
        ax2=fig.add_axes([x,y,w,w/ar*(FIGW/FIGH)]); ax2.imshow(im); ax2.axis('off')
        ax2.text(0.5,-0.05,cap,transform=ax2.transAxes,fontsize=9,ha='center',color=GRAY,fontproperties=zh)
    pdf.savefig(fig); plt.close(fig)

    # ===== 第5页 段级相关性 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '光钟比对：潮汐引力红移相关性（段级）')
    for path,x,y,w,cap in [
        ('clock/segment_analysis/batch_forest.png',0.04,0.30,0.46,'14段幅度比 A ± u_A（森林图）'),
        ('clock/segment_analysis/batch_shared_axis.png',0.52,0.20,0.44,'逐段拍频 vs 潮汐模板'),
    ]:
        im=Image.open(PRJ+path); ar=im.size[0]/im.size[1]
        ax2=fig.add_axes([x,y,w,w/ar*(FIGW/FIGH)]); ax2.imshow(im); ax2.axis('off')
        ax2.text(0.5,-0.04,cap,transform=ax2.transAxes,fontsize=9,ha='center',color=GRAY,fontproperties=zh)
    text_block(fig, 0.04, 0.15, '段级幅度拟合：12/14 段为负，跨段合并 Stouffer |z|=6.33（p=2.5e-10），幅度比 A=−0.52±0.08（6.8σ）', size=12)
    pdf.savefig(fig); plt.close(fig)

    # ===== 第6页 宏观正相关 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '14 组会话宏观正相关（更鲁棒信号）')
    for path,x,y,w,cap in [
        ('clock/correlation.png',0.04,0.30,0.42,'会话 y_i vs 潮汐频差相关性'),
        ('clock/clock_tidal_shift.png',0.50,0.30,0.46,'14 组会话平均潮汐频差'),
    ]:
        im=Image.open(PRJ+path); ar=im.size[0]/im.size[1]
        ax2=fig.add_axes([x,y,w,w/ar*(FIGW/FIGH)]); ax2.imshow(im); ax2.axis('off')
        ax2.text(0.5,-0.04,cap,transform=ax2.transAxes,fontsize=9,ha='center',color=GRAY,fontproperties=zh)
    text_block(fig, 0.04, 0.18,
        '• 会话级 yᵢ = Rᵢ/R_ref − 1 由 MATLAB 处理程序精确计算（2404–2408 行）\n'
        '• Pearson r = +0.472（p=0.088），10/14 同号 — 正向、与理论引力红移方向一致', size=11)
    pdf.savefig(fig); plt.close(fig)

    # ===== 第7页 环外+温度 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '光纤链路环外数据 + 天周期温度影响')
    for path,x,y,w,cap in [
        ('clock/temperature/fx_b2_lock_fraction.png',0.04,0.42,0.46,'环外10MHz信号(FXE_B2)逐日锁定比例'),
        ('clock/temperature/fx_b4_vs_temperature.png',0.04,0.20,0.46,'超稳参考 FXE_B4 vs 温度（无耦合）'),
    ]:
        im=Image.open(PRJ+path); ar=im.size[0]/im.size[1]
        ax2=fig.add_axes([x,y,w,w/ar*(FIGW/FIGH)]); ax2.imshow(im); ax2.axis('off')
        ax2.text(0.5,-0.05,cap,transform=ax2.transAxes,fontsize=9,ha='center',color=GRAY,fontproperties=zh)
    text_block(fig, 0.54, 0.50,
        '• 环外10MHz信号：约半数日子锁定，\n   半数偶发失锁/跳变（非温度）\n'
        '• 天周期温度影响在拍频中不可检出\n   （FXE_B8 鲁棒日峰峰仅 0.008 Hz）\n'
        '• 温度通过链路时延/相位噪声起作用，\n   不影响潮汐检出结论', size=10.5)
    pdf.savefig(fig); plt.close(fig)

    # ===== 第8页 方法论证 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '方法论证：PDF/MATLAB 源码 + 噪声模型')
    text_block(fig, 0.06, 0.78,
        '• MATLAB/PDF 处理链：shift_a（5个Sr系统修正）+ delta_g（静态引力红移）都是静态项\n'
        '• → 时变潮汐未显式扣除，残留在实测拍频 Dr = COEF·mean_dm 里\n'
        '• → 与「潮汐通过拍频检出」的分析框架自洽，互为印证 ✓\n'
        '• PDF 的 excess scatter ξ≈2–3×10⁻¹⁸（Birge=1.42）与潮汐幅度 A=−0.52 量级吻合\n'
        '• 噪声模型：链路白相位(1/τ) + 钟白频率(1/√τ)，非 1/f 闪烁平台\n'
        '• 段内算法交叉验证（直接匹配/三角/矩形/相位域 cumsum）：结论稳健不变\n'
        '• 优化滤波（预白化/换窗）不能突破 3.6× 信噪比墙 —— 已知信号最优线性提取 = 匹配滤波',
        size=12, color='#222')
    pdf.savefig(fig); plt.close(fig)

    # ===== 第9页 结论 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '结论')
    text_block(fig, 0.08, 0.74,
        '1. 潮汐引力红移被检出：段级 12/14 负相关，|z|=6.33（p=2.5e-10），A=−0.52±0.08（6.8σ）\n\n'
        '2. 会话级宏观正相关 r=+0.472（10/14 同号）— 与理论方向一致、更鲁棒\n\n'
        '3. 海潮负荷修正 3.9×（专业序列），固体潮波形完全一致\n\n'
        '4. 噪声本底 = 钟白频率噪声(1/√τ)，链路白相位(1/τ) 不影响潮汐检测\n\n'
        '5. 温度影响不可检出，不改变潮汐结论', size=14, color='#222')
    pdf.savefig(fig); plt.close(fig)

    # ===== 第10页 建议 =====
    fig = figpage()
    ax = fig.add_axes([0,0,1,1]); title_bar(ax, '建议：如何提升检测力与产出的方向')
    text_block(fig, 0.08, 0.76,
        '1. 定死 s_beat 符号（梳尺/本振频率高低）— 0 成本，确定潮汐物理方向\n\n'
        '2. 两钟直接比对代替 1550nm 传递链路拍频 — 去掉链路白相位噪声、降本底\n\n'
        '3. 增加独立实验段数 N（u_A ∝ 1/√N）：~33段→10%精度，~133段→5%，~368段→3%\n\n'
        '4. 采集链路双向时延 / 机架温度日志 — 量化温度-链路耦合\n\n'
        '5. 确认高程差项 u_H（PDF 标注待定）与潮汐 ΔW 同量级，显式核算避免混淆\n\n'
        '滤波算法已接近最优（匹配滤波），提升靠「加段数+降本底+定符号」而非换滤波',
        size=13, color='#222')
    pdf.savefig(fig); plt.close(fig)

print("PDF saved: /tmp/opencode/ppt_build/summary2.pdf")
