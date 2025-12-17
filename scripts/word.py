import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import datetime
import textwrap
import io

# --- 配置参数 (2016-2025) ---
YEARS = range(2016, 2026)  # 包含 2016 到 2025 共 10 年
YEARS_LEFT = YEARS[:5]
YEARS_RIGHT = YEARS[5:]
COLUMNS = 2

# --- 优化后的配色方案 ---
COLOR_BG_LIGHT = '#F4F1EA'  # 修改点 2：将主背景色修改为更浅的米白色
COLOR_TEXT_DARK = '#2D4739'  # 正文和制表人信息
COLOR_TITLE_DARK = '#121619'  # 标题和重要线条
COLOR_ACCENT_LINE = '#BCB382'  # 年份标题边框/细分隔线
COLOR_HIGHLIGHT = '#47340C'  # 年份标题和问题强调色

FONT_PATH = "./font.ttf"


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

    creative_records = {}
    data_start_index = 4
    for i, year in enumerate(YEARS):
        start = data_start_index + i * 4
        creative_records[year] = {
            "cp_work": args[start],
            "style_excerpt": args[start + 1],
            "major_impact": args[start + 2],
            "reflection": args[start + 3],
        }

    # 2. 图片绘制配置
    W = 1600
    MARGIN = 50
    GUTTER = 40
    COLUMN_WIDTH = (W - 2 * MARGIN - GUTTER) // COLUMNS
    TEXT_WIDTH = COLUMN_WIDTH - 40

    try:
        font_title = ImageFont.truetype(FONT_PATH, 55)
        font_year = ImageFont.truetype(FONT_PATH, 30)
        font_header = ImageFont.truetype(FONT_PATH, 25)
        font_text = ImageFont.truetype(FONT_PATH, 20)
        font_base = ImageFont.truetype(FONT_PATH, 20)
    except IOError:
        font_title = ImageFont.load_default()
        font_year = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_base = ImageFont.load_default()

    line_height = 30

    def get_text_height(text, font, max_width):
        if not text:
            return line_height
        chars_per_line = int(max_width / (font.size * 0.9))
        lines = textwrap.wrap(text, width=chars_per_line, replace_whitespace=False)
        return len(lines) * line_height + 15

    def calculate_year_height(year):
        record = creative_records[year]
        h = 0
        h += 50
        h += 30
        h += 4 * line_height
        h += get_text_height(record["cp_work"], font_text, TEXT_WIDTH)
        h += get_text_height(record["style_excerpt"], font_text, TEXT_WIDTH)
        h += get_text_height(record["major_impact"], font_text, TEXT_WIDTH)
        h += get_text_height(record["reflection"], font_text, TEXT_WIDTH)
        h += 4 * 20
        h += 40
        return h

    H_base = 200
    H_left_content = sum(calculate_year_height(year) for year in YEARS_LEFT)
    H_right_content = sum(calculate_year_height(year) for year in YEARS_RIGHT)
    H_content = max(H_left_content, H_right_content)
    H = H_base + H_content + 50

    img = Image.new('RGB', (W, H), color=COLOR_BG_LIGHT)
    draw = ImageDraw.Draw(img)

    y_cursor = 50
    title_text = base_info['title']
    draw.text((W / 2, y_cursor), title_text, fill=COLOR_TITLE_DARK, anchor="ms", font=font_title)
    y_cursor += 70

    draw.text((MARGIN, y_cursor), f"填表人: {base_info['writer']}", fill=COLOR_TEXT_DARK, font=font_base)
    draw.text((W / 2, y_cursor), f"填写时间: {base_info['date']}", fill=COLOR_TEXT_DARK, anchor="mt", font=font_base)
    draw.text((W - MARGIN, y_cursor), f"制表人: {base_info['creator']}", fill=COLOR_TEXT_DARK, anchor="rt",
              font=font_base)

    y_cursor += 50
    draw.line((MARGIN, y_cursor, W - MARGIN, y_cursor), fill=COLOR_TITLE_DARK, width=2)
    y_cursor += 40

    def draw_year_records(years_list, x_start, y_start_initial):
        y_cursor_col = y_start_initial

        for i, year in enumerate(years_list):
            record = creative_records[year]

            # 修改点 1：去掉了绘制 COLOR_ALT_BG 交替背景色的逻辑

            draw.text((x_start, y_cursor_col + 5), f"🌟 【 {year} 年 创作小结 】", fill=COLOR_HIGHLIGHT, font=font_year)

            y_cursor_col += 50
            y_cursor_col += 30

            for question, key, color in [
                ("(1) 本年我在写：", "cp_work", COLOR_HIGHLIGHT),
                ("(2) 最能代表我本年风格的段落是：", "style_excerpt", COLOR_HIGHLIGHT),
                ("(3) 本年对我创作影响最大的事是：", "major_impact", COLOR_HIGHLIGHT),
                ("(4) 本年创作的总结感想是：", "reflection", COLOR_HIGHLIGHT)
            ]:
                draw.text((x_start, y_cursor_col), question, fill=color, font=font_header)
                y_cursor_col += line_height

                content = record[key]
                if content:
                    chars_per_line = int(TEXT_WIDTH / (font_text.size * 0.9))
                    lines = textwrap.wrap(content, width=chars_per_line, replace_whitespace=False)
                    for line in lines:
                        draw.text((x_start + 10, y_cursor_col), line, fill=COLOR_TEXT_DARK, font=font_text)
                        y_cursor_col += line_height
                else:
                    draw.text((x_start + 10, y_cursor_col), "(暂无内容)", fill=COLOR_TEXT_DARK, font=font_text)
                    y_cursor_col += line_height

                y_cursor_col += 20

            draw.line((x_start + 50, y_cursor_col - 10, x_start + COLUMN_WIDTH - 50, y_cursor_col - 10),
                      fill=COLOR_ACCENT_LINE, width=1)
            y_cursor_col += 40

        return y_cursor_col

    X_START_LEFT = MARGIN
    X_START_RIGHT = MARGIN + COLUMN_WIDTH + GUTTER

    draw_year_records(YEARS_LEFT, X_START_LEFT, y_cursor)
    draw_year_records(YEARS_RIGHT, X_START_RIGHT, y_cursor)

    center_x = X_START_LEFT + COLUMN_WIDTH + GUTTER / 2
    draw.line((center_x, y_cursor, center_x, H - 50), fill=COLOR_TEXT_DARK, width=2)

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
            gr.Markdown("### 先在本页填写基本信息，随后切换到年份标签进行记录。")
            title_box = gr.Textbox(value="创作者十年变化总结表", interactive=False, label="总结表标题")
            creator_box = gr.Textbox(label="制表人", interactive=False, value="南极冰雕师")
            writer_box = gr.Textbox(label="填表人", lines=1, placeholder="可选")
            date_box = gr.Textbox(label="填写时间", lines=1, value=datetime.date.today().strftime("%Y年%m月%d日"),
                                  interactive=True)
            all_inputs.extend([title_box, creator_box, writer_box, date_box])

        for year in YEARS:
            with gr.TabItem(f"✒️ {year} "):
                gr.Markdown(f"### <span style='color: {COLOR_HIGHLIGHT};'>【 {year} 年创作记录 】</span>")
                cp_work = gr.Textbox(label="1. 本年我在写（cp/作品……）：", lines=2)
                style_excerpt = gr.Textbox(label="2. 最能代表我本年风格的段落是：", lines=8)
                major_impact = gr.Textbox(label="3. 本年对我创作影响最大的事是：", lines=3)
                reflection = gr.Textbox(label="4. 我对本年创作的总结感想是：", lines=5)
                all_inputs.extend([cp_work, style_excerpt, major_impact, reflection])

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