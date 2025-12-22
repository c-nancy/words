import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import datetime
import textwrap
import io
import os

# --- 配置参数 (2016-2025) ---
YEARS = range(2016, 2026)
YEARS_LEFT = YEARS[:5]
YEARS_RIGHT = YEARS[5:]
COLUMNS = 2

# --- 优化后的配色方案 ---
COLOR_BG_LIGHT = '#F4F1EA'
COLOR_TEXT_DARK = '#2D4739'
COLOR_TITLE_DARK = '#121619'
COLOR_ACCENT_LINE = '#BCB382'
COLOR_HIGHLIGHT = '#47340C'

FONT_PATH = "./scripts/font.ttf"


# --- 辅助函数：处理换行并绘制文本 ---
def draw_multiline_text(draw, text, start_x, start_y, font, fill, max_char_width=28, line_height=35):
    """
    处理原始文本中的换行符，并支持自动折行。
    返回绘制完成后的结束 Y 坐标。
    """
    if not text:
        draw.text((start_x, start_y), "(暂无内容)", font=font, fill=fill)
        return start_y + line_height

    # 首先按照用户输入的手动换行符拆分
    paragraphs = text.split('\n')
    current_y = start_y

    for p in paragraphs:
        if p.strip() == "":
            current_y += line_height  # 保留空行
            continue

        # 对每一段进行自动折行
        wrapped_lines = textwrap.wrap(p, width=max_char_width)
        for line in wrapped_lines:
            draw.text((start_x, current_y), line, font=font, fill=fill)
            current_y += line_height

    return current_y


def calc_text_height(text, max_char_width=28, line_height=35):
    """预计算包含换行符的文本高度"""
    if not text:
        return line_height
    paragraphs = text.split('\n')
    total_lines = 0
    for p in paragraphs:
        if p.strip() == "":
            total_lines += 1
        else:
            wrapped_lines = textwrap.wrap(p, width=max_char_width)
            total_lines += len(wrapped_lines)
    return total_lines * line_height


# --- 核心图片生成函数 ---

def generate_summary_image(*args):
    """接收所有输入参数并生成一张美化的总结长图。"""

    # 1. 数据解析
    base_info = {
        "title": args[0],
        "creator": args[1],
        "writer": args[2],
        "date": args[3]
    }

    # 每一年的数据占据 args 的 4 个位置
    years_data = {}
    for i, year in enumerate(YEARS):
        start_idx = 4 + i * 4
        years_data[year] = {
            "q1": args[start_idx],
            "q2": args[start_idx + 1],
            "q3": args[start_idx + 2],
            "q4": args[start_idx + 3]
        }

    # 2. 动态布局计算
    try:
        font_title = ImageFont.truetype(FONT_PATH, 55)
        font_subtitle = ImageFont.truetype(FONT_PATH, 22)
        font_year = ImageFont.truetype(FONT_PATH, 32)
        font_q = ImageFont.truetype(FONT_PATH, 24)
        font_content = ImageFont.truetype(FONT_PATH, 20)
    except:
        font_title = font_subtitle = font_year = font_q = font_content = ImageFont.load_default()

    WIDTH = 1600
    MARGIN = 60
    GUTTER = 50
    COLUMN_WIDTH = (WIDTH - 2 * MARGIN - GUTTER) // 2

    def get_year_block_height(year_val):
        h = 80  # 年份标题高度
        data = years_data[year_val]
        for q_key in ["q1", "q2", "q3", "q4"]:
            h += 35  # 问题标题高度
            h += calc_text_height(data[q_key]) + 20  # 文本内容高度 + 间距
        return h + 60  # 模块底部留白

    left_h = sum(get_year_block_height(y) for y in YEARS_LEFT)
    right_h = sum(get_year_block_height(y) for y in YEARS_RIGHT)

    CONTENT_TOP = 240
    H = CONTENT_TOP + max(left_h, right_h) + 100

    # 3. 开始绘图
    img = Image.new('RGB', (WIDTH, H), COLOR_BG_LIGHT)
    draw = ImageDraw.Draw(img)

    # 绘制顶栏
    draw.text((WIDTH // 2, 80), base_info["title"], font=font_title, fill=COLOR_TITLE_DARK, anchor="mm")
    draw.text((MARGIN, 160), f"填表人: {base_info['writer'] or '未填写'}", font=font_subtitle, fill=COLOR_TEXT_DARK)
    draw.text((WIDTH // 2, 160), f"填写时间: {base_info['date']}", font=font_subtitle, fill=COLOR_TEXT_DARK,
              anchor="mm")
    draw.text((WIDTH - MARGIN, 160), f"制表人: {base_info['creator']}", font=font_subtitle, fill=COLOR_TEXT_DARK,
              anchor="rm")
    draw.line((MARGIN, 200, WIDTH - MARGIN, 200), fill=COLOR_TITLE_DARK, width=2)

    def draw_col(years_list, start_x, start_y):
        y = start_y
        for year in years_list:
            # 绘制年份标题
            draw.text((start_x, y + 20), f"🌟 【 {year} 年 创作小结 】", font=font_year, fill=COLOR_HIGHLIGHT)
            y += 85

            data = years_data[year]
            questions = [
                ("1. 本年我在写：", data["q1"]),
                ("2. 风格段落：", data["q2"]),
                ("3. 重大影响：", data["q3"]),
                ("4. 总结感想：", data["q4"])
            ]

            for q_title, answer in questions:
                draw.text((start_x, y), q_title, font=font_q, fill=COLOR_HIGHLIGHT)
                y += 35
                # 调用支持换行的绘制函数
                y = draw_multiline_text(draw, answer, start_x + 15, y, font_content, COLOR_TEXT_DARK)
                y += 20

            # 装饰线
            draw.line((start_x + 50, y, start_x + COLUMN_WIDTH - 50, y), fill=COLOR_ACCENT_LINE, width=1)
            y += 55

    draw_col(YEARS_LEFT, MARGIN, CONTENT_TOP)
    draw_col(YEARS_RIGHT, MARGIN + COLUMN_WIDTH + GUTTER, CONTENT_TOP)

    # 绘制中央垂直分隔线
    mid_x = MARGIN + COLUMN_WIDTH + (GUTTER // 2)
    draw.line((mid_x, CONTENT_TOP, mid_x, H - 80), fill=COLOR_TITLE_DARK, width=2)

    return img


with gr.Blocks(
        title="创作者十年变化总结表",
        css=f"body {{ background-color: {COLOR_BG_LIGHT}; }} .gradio-container {{ background-color: {COLOR_BG_LIGHT}; }}",
        theme=gr.themes.Soft(primary_hue="stone", secondary_hue="gray")
) as app:
    gr.Markdown(f"# <span style='color: {COLOR_TITLE_DARK};'>✍️ 创作者十年变化总结表</span>")

    all_inputs = []

    with gr.Tabs():
        with gr.TabItem("📝 基础信息"):
            with gr.Column():
                title_box = gr.Textbox(label="总结表标题", value="创作者十年变化总结表", interactive=False)
                creator_box = gr.Textbox(label="制表人", value="南极冰雕师", interactive=False)
                writer_box = gr.Textbox(label="填表人", placeholder="请输入您的笔名")
                date_box = gr.Textbox(label="填写时间", value=datetime.date.today().strftime("%Y年%m月%d日"))
                all_inputs.extend([title_box, creator_box, writer_box, date_box])

        for year in YEARS:
            with gr.TabItem(f"✒️ {year}"):
                gr.Markdown(f"### <span style='color: {COLOR_HIGHLIGHT};'>【 {year} 年创作记录 】</span>")
                q1 = gr.Textbox(label="1. 本年我在写（cp/作品……）：", lines=2)
                q2 = gr.Textbox(label="2. 最能代表我本年风格的段落是：", lines=8)
                q3 = gr.Textbox(label="3. 本年对我创作影响最大的事是：", lines=3)
                q4 = gr.Textbox(label="4. 我对本年创作的总结感想是：", lines=5)
                all_inputs.extend([q1, q2, q3, q4])

        with gr.TabItem("🖼️ 完成与导出"):
            gr.Markdown("### 确认所有内容已填写后，点击下方按钮生成最终长图。")
            generate_button = gr.Button("生成十年总结图", variant="primary")
            output_image = gr.Image(label="十年总结", type="pil", format="png", width="auto", height="auto")

    gr.Markdown(f"""
    ---
    ### 说明：
    1. **数据安全**：系统**不会自动保存**填写的内容，请务必不要在填写中途刷新网页，建议在本地备份长文本。
    2. **内容留空**：表单中的各项均可不填。若某项留空，导出图片时该位置会自动显示“**（暂无内容）**”。
    3. **最佳效果**：建议“风格段落”字数控制在 150-300 字左右，以获得最美观的排版间距。
    4. **图片保存**：生成成功后，右键点击图片即可选择“另存为”保存到本地。
    """)

    generate_button.click(fn=generate_summary_image, inputs=all_inputs, outputs=output_image)

if __name__ == "__main__":
    app.launch()