import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import os

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="PRO부동산 매물 카드 생성기", page_icon="🏢")

# --- 2. 유틸리티 함수 ---
def safe_float(value):
    if not value: return 0.0
    try:
        # 문자열일 경우 쉼표 제거 등 처리, 이미 숫자면 그대로 반환
        clean_val = re.sub(r'[^0-9.]', '', str(value))
        return float(clean_val) if clean_val else 0.0
    except: return 0.0

def format_num(value):
    try:
        val = float(value)
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(value)

def draw_multicolor_centered(draw, x, y, parts, font, anchor_y="m"):
    total_width = 0
    for text, color in parts:
        total_width += draw.textlength(text, font=font)
    
    current_x = x - (total_width / 2)
    anchor_style = f"l{anchor_y}"
    
    for text, color in parts:
        draw.text((current_x, y), text, fill=color, font=font, anchor=anchor_style)
        current_x += draw.textlength(text, font=font)

def draw_val_unit_億(draw, x, y, value, font_val, font_unit, color):
    val_str = format_num(value)
    w_val = draw.textlength(val_str, font=font_val)
    w_unit = draw.textlength("억", font=font_unit)
    start_x = x - ((w_val + w_unit) / 2)
    draw.text((start_x, y), val_str, fill=color, font=font_val, anchor="lm")
    draw.text((start_x + w_val, y + 12), "억", fill=color, font=font_unit, anchor="lm")

def draw_adaptive_text(draw, x, y, text, font_candidates, color, max_width, anchor="mm"):
    selected_font = font_candidates[-1]
    for font in font_candidates:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width:
            selected_font = font
            break
    draw.text((x, y), text, fill=color, font=selected_font, anchor=anchor)

# --- 3. 데이터 ---
ZONE_DATA = {
    "1구역": ["관처 준비중 (25.9월 총회완료)", "조합원분양가: 59타입 8.5억 / 84타입 10.5억", "이주비 최대 90% 지급예정 (무60%+유30%)", "84기준 입주시 예상시세 30억 이상 예상", "추가분담금 납부조건: 10 : 0 : 90 (예정)", "3.5", "8,400만원"],
    "2구역": ["착공 준비중 (재분양신청 완료)", "조합원분양가: 59타입 7.5억 / 84타입 9.1억", "이주비 지급조건: 감정평가금액의 최대 60%", "109기준 입주시 예상시세 MIN 32억 예상", "추가분담금 납부조건: 0 : 0 : 100 (입주시 완납)", "3.5", "9,100만원"],
    "3구역": ["관리처분인가 임박 (26년2월 예정)", "조합원분양가: 59타입 8.4억 / 84타입 10.3억", "이주비 지급조건: 감정가 최대 100% 지급예정", "84기준 입주시 예상시세 MIN 30억 예상", "추가분담금 납부조건: 0 : 0 : 100 (입주시 완납)", "3.5", "10,300만원"],
    "4구역": ["철거마무리 (멸실등기 예정)", "조합원분양가: 59타입 7.5억 / 84타입 9억", "이주비 지급조건: 감정평가금액의 최대 70%", "84기준 입주시 예상시세 MIN 30억 예상", "추가분담금 납부조건: 10 : 30 : 60 (계약/중도/잔금)", "3.5", "9,000만원"],
    "5구역": ["철거준비중 (일반이주 완료)", "조합원분양가: 59타입 8억 / 84타입 10억", "이주비 지급조건: 감정평가금액의 최대 60%", "84기준 입주시 예상시세 MIN 30억 예상", "추가분담금 납부조건: 10 : 30 : 60 (계약/중도/잔금)", "3.5", "10,000만원"],
    "6구역": ["착공 중 (멸실등기완료)", "조합원분양가: 59타입 5.7억 / 84타입 6.8억", "이주비 지급조건: 감정평가금액의 최대 60%", "84기준 입주시 예상시세 MIN 30억 예상", "추가분담금 납부조건: 0 : 0 : 100 (입주시 완납)", "3.5", "6,800만원"],
    "7구역": ["이주 마무리 (12월 철거예정)", "조합원분양가: 59타입 8억 / 84타입 10억", "이주비 지급조건: 감정평가금액의 최대 60%", "84기준 입주시 예상시세 MIN 28억 예상", "추가분담금 납부조건: 0 : 0 : 100 (입주시 완납)", "3.5", "10,000만원"],
    "8구역": ["착공중", "조합원분양가: 59타입 8억 / 84타입 9.5억", "이주비 지급조건: 감정평가금액의 최대 60%", "84기준 입주시 예상시세 MIN 30억 예상", "추가분담금 납부조건: 10 : 30 : 60 (계약/중도/잔금)", "3.5", "9,500만원"]
}

# --- 4. Streamlit UI ---
st.title("🏢 PRO부동산 매물 카드 생성기")
st.caption("PC/모바일 어디서든 접속하여 매물 카드를 생성하세요.")

# 세션 상태 초기화 (데이터 저장소)
if 'init' not in st.session_state:
    st.session_state.init = True
    # 초기값 설정
    st.session_state.p_sale = "24"
    st.session_state.p_premium = "15"
    st.session_state.p_rent = "18"
    st.session_state.tax_rate = "3.5"
    st.session_state.tax_val = "8,400만원"
    st.session_state.p_total = "28"
    st.session_state.p_margin = "10"

# 구역 선택
selected_zone = st.selectbox("구역 선택", list(ZONE_DATA.keys()))

# 구역 변경 시 기본값 자동 세팅
if 'last_zone' not in st.session_state or st.session_state.last_zone != selected_zone:
    st.session_state.last_zone = selected_zone
    zone_info = ZONE_DATA[selected_zone]
    # 리스트 내용은 나중에 이미지 생성 시 직접 참조
    st.session_state.tax_rate = zone_info[5]
    st.session_state.tax_val = zone_info[6]

# 입력 폼
with st.form("input_form"):
    st.subheader("1. 매물 정보 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        prop_type = st.text_input("매물 타입", value="1+1")
        p_sale = st.text_input("4. 매매가 (억)", value=st.session_state.p_sale)
        p_rent = st.text_input("7. 임대 (억)", value=st.session_state.p_rent)
        p_total = st.text_input("8. 총 매수가 (억)", value=st.session_state.p_total)
    
    with col2:
        invest_price = st.text_input("3. 초기투자금 (자동/수동)", value=format_num(safe_float(p_sale) - safe_float(p_rent)))
        p_premium = st.text_input("5. 프리미엄 (억)", value=st.session_state.p_premium)
        p_rights = st.text_input("6. 권리가 (자동/수동)", value=format_num(safe_float(p_sale) - safe_float(p_premium)))
        p_margin = st.text_input("9. 안전마진 (억)", value=st.session_state.p_margin)

    st.markdown("---")
    st.subheader("2. 취득세 및 상세 정보")
    
    col_tax1, col_tax2 = st.columns([1, 2])
    with col_tax1:
        tax_rate = st.text_input("세율(%)", value=st.session_state.tax_rate)
    with col_tax2:
        # 취득세 자동 계산 로직
        current_tax_val = st.session_state.tax_val
        # 세율이나 매매가가 바뀌면 자동 계산 시도
        if tax_rate and p_sale:
             calc_tax = int(safe_float(p_sale) * safe_float(tax_rate) * 100)
             current_tax_val = f"{calc_tax:,}만원"
        
        final_tax_str = st.text_input("취득세 결과 (수정 가능)", value=current_tax_val)

    # 상세 리스트 (구역 데이터에서 가져오되 수정 가능하게)
    st.caption("상세 리스트 내용")
    list_inputs = []
    zone_defaults = ZONE_DATA[selected_zone]
    for i in range(5):
        list_inputs.append(st.text_input(f"L{i+1}", value=zone_defaults[i]))

    col3, col4 = st.columns(2)
    with col3:
        comp_type = st.text_input("구성 타입", value="84㎡")
    with col4:
        contact = st.text_input("연락처", value="010.2319.0977")

    submitted = st.form_submit_button("📸 매물 카드 생성하기", type="primary")

# --- 5. 이미지 생성 및 다운로드 ---
if submitted:
    # 폰트 로드 (Streamlit Cloud 배포 시 경로 주의)
    # 로컬에선 같은 폴더, 서버에선 업로드 필요
    font_path = "malgunbd.ttf"
    if not os.path.exists(font_path):
        # 폰트 파일이 없으면 경고 메시지 출력 후 기본 폰트 사용 (디자인 깨질 수 있음)
        st.warning("⚠️ 'malgunbd.ttf' 폰트 파일이 없습니다. 기본 폰트를 사용합니다.")
        font_path = None # PIL 기본 폰트 사용

    try:
        width, height = 1300, 950
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Colors & Fonts
        BLACK, WHITE, YELLOW, RED = (0, 0, 0), (255, 255, 255), (255, 255, 0), (255, 20, 20)
        GRAY_BG, PINK_BG = (240, 240, 240), (255, 230, 230)
        TRANSPARENT_EMERALD = (210, 255, 230, 128)
        TRANSPARENT_SKY = (225, 245, 255, 128)
        
        def get_font(size):
            if font_path: return ImageFont.truetype(font_path, size)
            return ImageFont.load_default()

        f_header = get_font(95); f_brand = get_font(35)
        f_invest_val = get_font(115); f_invest_label = get_font(70); f_invest_unit = get_font(50)
        f_table_head = get_font(35); f_table_val = get_font(85); f_table_unit = get_font(35)
        f_list_sm = [get_font(38), get_font(34), get_font(26)]
        f_list_label_matched = get_font(38)
        f_right_sm = get_font(23); f_right_md = get_font(35)
        f_right_lg = get_font(65); f_right_contact = get_font(35)
        f_footer = get_font(35); f_platform = [get_font(21), get_font(18)]
        f_tax_val = get_font(40)

        # Drawing Logic (v61 Codebase)
        draw.rectangle([(0, 0), (width, 160)], fill=BLACK)
        brand_x_center = 150
        draw.text((brand_x_center, 60), "대한민국 부동산", fill=WHITE, font=f_brand, anchor="mm")
        header_parts = [("NO.1", YELLOW), (" 플랫폼", WHITE)]
        draw_multicolor_centered(draw, brand_x_center, 110, header_parts, f_brand, anchor_y="m")
        draw.text((width/2 - 10, 80), f"노량진 {selected_zone}", fill=WHITE, font=f_header, anchor="mm")
        draw.text((width/2 + 410, 80), prop_type, fill=YELLOW, get_font(100), anchor="mm")

        draw.rectangle([(0, 160), (width, 330)], fill=YELLOW)
        draw.text((width/2 - 250, 245), "초기투자금 :", fill=RED, font=f_invest_label, anchor="mm")
        draw_val_unit_億(draw, width/2 + 150, 245, invest_price, f_invest_val, f_invest_unit, RED)

        table_y, col_w = 330, width / 6
        draw.rectangle([(0, table_y), (col_w*4, table_y + 70)], fill=GRAY_BG)
        draw.rectangle([(0, table_y + 70), (col_w*4, table_y + 190)], fill=WHITE)
        draw.rectangle([(col_w*4, table_y), (width, table_y + 190)], fill=PINK_BG)
        cols, vals = ["매매가", "프리미엄", "권리가", "임대", "총 매수가", "안전마진"], [p_sale, p_premium, p_rights, p_rent, p_total, p_margin]
        for i in range(6):
            x = i * col_w
            draw.text((x + col_w/2, table_y + 35), cols[i], fill=BLACK, font=f_table_head, anchor="mm")
            color_val = RED if i == 1 else BLACK
            draw_val_unit_億(draw, x + col_w/2, table_y + 130, vals[i], f_table_val, f_table_unit, color_val)

        detail_y, split_x = 520, col_w * 4
        row_height = 72
        
        for i, text in enumerate(list_inputs):
            cur_y = detail_y + 35 + (i * row_height)
            bg_color = GRAY_BG if i % 2 == 0 else WHITE
            y_start = detail_y + (i * row_height) - 1
            if i == 0: y_start -= 1 
            y_end = detail_y + ((i + 1) * row_height) + 1
            draw.rectangle([(0, y_start), (split_x, y_end)], fill=bg_color)
            draw.rectangle([(24, cur_y - 6), (36, cur_y + 6)], fill=BLACK)
            color_use = RED if i == 0 else BLACK
            if i == 0 and ":" in text:
                parts = text.split(":", 1)
                draw.text((60, cur_y), parts[0] + ":", fill=color_use, font=f_list_label_matched, anchor="lm")
                label_w = draw.textlength(parts[0] + ":", font=f_list_label_matched)
                draw_adaptive_text(draw, 60 + label_w + 10, cur_y, parts[1], f_list_sm, color_use, split_x - 80 - label_w, anchor="lm")
            else:
                draw_adaptive_text(draw, 60, cur_y, text, f_list_sm, color_use, split_x - 80, anchor="lm")

        overlay = Image.new('RGBA', image.size, (0,0,0,0)); drw_overlay = ImageDraw.Draw(overlay)
        drw_overlay.rectangle([(split_x, detail_y), (width, detail_y + 70)], fill=TRANSPARENT_EMERALD)
        drw_overlay.rectangle([(split_x, detail_y + 70), (width, detail_y + 230)], fill=TRANSPARENT_SKY)
        image.paste(overlay, (0,0), overlay)
        
        sub_split, mid_y = col_w * 5, detail_y + 70
        draw.text((split_x + (sub_split-split_x)/2, detail_y + 35), "취득세(예상)", fill=BLACK, font=f_right_sm, anchor="mm")
        draw.text((sub_split + (width-sub_split)/2, detail_y + 35), final_tax_str, fill=BLACK, font=f_tax_val, anchor="mm")
        draw.text((split_x + (width-split_x)/2, mid_y + 80), comp_type, fill=BLACK, font=f_right_lg, anchor="mm")
        bot_y_start = mid_y + 160
        draw_adaptive_text(draw, split_x + (width-split_x)/2, bot_y_start + 32, "대한민국 재개발 재건축 NO.1 플랫폼", f_platform, BLACK, width-split_x-10, anchor="mm")
        draw.text((split_x + (width-split_x)/2, 840), f"서프로 : {contact}", fill=BLACK, font=f_right_contact, anchor="mm")

        draw.rectangle([(0, 880), (width, 950)], fill=BLACK)
        footer_parts = [(f"노량진{selected_zone} ", WHITE), ("가장 최신", RED), (" 진행상황은 아래▼ 자세히 나와있습니다.", WHITE)]
        draw_multicolor_centered(draw, width/2, 915, footer_parts, f_footer, anchor_y="m")

        for i in range(1, 6): draw.line([(i * col_w, table_y), (i * col_w, table_y + 190)], fill=BLACK, width=2)
        for yp in [table_y, table_y+70, table_y+190]: draw.line([(0, yp), (width, yp)], fill=BLACK, width=2)
        for i in range(5):
            cur_y = detail_y + 35 + (i * row_height)
            draw.rectangle([(20, cur_y - 10), (40, cur_y + 10)], outline=BLACK, width=3)
        draw.line([(split_x, detail_y), (split_x, 880)], fill=BLACK, width=2)
        draw.line([(split_x, detail_y), (width, detail_y)], fill=BLACK, width=2)
        draw.line([(split_x, detail_y + 70), (width, detail_y + 70)], fill=BLACK, width=2)
        draw.line([(sub_split, detail_y), (sub_split, detail_y + 70)], fill=BLACK, width=2)
        draw.line([(split_x, mid_y + 160), (width, mid_y + 160)], fill=BLACK, width=2)
        mid_bottom_y = bot_y_start + (880 - bot_y_start) / 2
        draw.line([(split_x, mid_bottom_y), (width, mid_bottom_y)], fill=BLACK, width=1)

        draw.rectangle([(0, 160), (6, 880)], fill=BLACK)
        draw.rectangle([(1294, 160), (1300, 880)], fill=BLACK)

        # Show & Download
        st.image(image, caption="생성된 매물 카드", use_column_width=True)
        
        # Save to buffer for download
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="⬇️ 이미지 다운로드 (핸드폰 저장)",
            data=byte_im,
            file_name=f"매물정보_{selected_zone}.png",
            mime="image/png",
            type="primary"
        )

    except Exception as e:
        st.error(f"오류 발생: {e}")
