import streamlit as st
from PIL import Image, ImageDraw
from io import BytesIO
from copy import deepcopy

st.set_page_config(page_title="PointKey MVP v3", layout="wide")

MAX_SCENARIOS = 10
DEFAULT_SCENARIOS = [
    {
        "name": "시나리오 1",
        "window_title": "",
        "window_text": "",
        "hotkey": "F1",
        "x": 0,
        "y": 0,
        "mode": "Move + Click",
        "note": "",
        "image_name": "",
        "img_w": 0,
        "img_h": 0,
    },
    {
        "name": "시나리오 2",
        "window_title": "",
        "window_text": "",
        "hotkey": "F2",
        "x": 0,
        "y": 0,
        "mode": "Move + Click",
        "note": "",
        "image_name": "",
        "img_w": 0,
        "img_h": 0,
    },
    {
        "name": "시나리오 3",
        "window_title": "",
        "window_text": "",
        "hotkey": "F3",
        "x": 0,
        "y": 0,
        "mode": "Move + Click",
        "note": "",
        "image_name": "",
        "img_w": 0,
        "img_h": 0,
    },
]

MODES = ["Move Only", "Move + Click", "Move + Double Click", "Move + Right Click"]
COORD_OPTIONS = ["Window", "Client", "Screen"]


def get_default_scenarios(count: int):
    items = []
    for i in range(count):
        base = deepcopy(DEFAULT_SCENARIOS[i]) if i < len(DEFAULT_SCENARIOS) else {
            "name": f"시나리오 {i+1}",
            "window_title": "",
            "window_text": "",
            "hotkey": f"F{i+1}",
            "x": 0,
            "y": 0,
            "mode": "Move + Click",
            "note": "",
            "image_name": "",
            "img_w": 0,
            "img_h": 0,
        }
        items.append(base)
    return items


def init_state() -> None:
    if "scenario_count" not in st.session_state:
        st.session_state.scenario_count = 3
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = get_default_scenarios(st.session_state.scenario_count)
    if "coord_mode" not in st.session_state:
        st.session_state.coord_mode = "Window"
    if "mouse_speed" not in st.session_state:
        st.session_state.mouse_speed = 0
    if "sleep_before" not in st.session_state:
        st.session_state.sleep_before = 0
    if "sleep_after_activate" not in st.session_state:
        st.session_state.sleep_after_activate = 100
    if "sleep_after_move" not in st.session_state:
        st.session_state.sleep_after_move = 0
    if "activation_timeout" not in st.session_state:
        st.session_state.activation_timeout = 2.0


def resize_scenarios(new_count: int) -> None:
    current = st.session_state.scenarios
    if new_count > len(current):
        current.extend(get_default_scenarios(new_count)[len(current):new_count])
    else:
        current = current[:new_count]
    st.session_state.scenarios = current
    st.session_state.scenario_count = new_count


def load_image(uploaded_file):
    if uploaded_file is None:
        return None
    return Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")


def draw_crosshair(image: Image.Image, x: int, y: int) -> Image.Image:
    img = image.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))

    # crosshair
    draw.line((max(0, x - 20), y, min(w - 1, x + 20), y), fill=(255, 0, 0), width=2)
    draw.line((x, max(0, y - 20), x, min(h - 1, y + 20)), fill=(255, 0, 0), width=2)
    draw.ellipse((x - 6, y - 6, x + 6, y + 6), outline=(255, 0, 0), width=2)
    return img


def build_winexist_expr(window_title: str, window_text: str) -> str:
    title = window_title.replace('"', '`"')
    text = window_text.replace('"', '`"')
    if text:
        return f'WinExist("{title}", "{text}")'
    return f'WinExist("{title}")'


def build_winactivate_line(window_title: str, window_text: str) -> str:
    title = window_title.replace('"', '`"')
    text = window_text.replace('"', '`"')
    if text:
        return f'WinActivate "{title}", "{text}"'
    return f'WinActivate "{title}"'


def build_winwaitactive_line(window_title: str, window_text: str, timeout: float) -> str:
    title = window_title.replace('"', '`"')
    text = window_text.replace('"', '`"')
    if text:
        return f'WinWaitActive "{title}", "{text}", {timeout}'
    return f'WinWaitActive "{title}", , {timeout}'


def generate_ahk(scenarios, coord_mode: str, mouse_speed: int, sleep_before: int, sleep_after_activate: int, sleep_after_move: int, activation_timeout: float) -> str:
    lines = [
        "#Requires AutoHotkey v2.0",
        f'CoordMode "Mouse", "{coord_mode}"',
        "",
    ]

    for scenario in scenarios:
        hotkey = scenario["hotkey"].strip()
        if not hotkey:
            continue

        name = scenario["name"].strip() or "Unnamed Scenario"
        window_title = scenario["window_title"].strip()
        window_text = scenario.get("window_text", "").strip()
        x = int(scenario["x"])
        y = int(scenario["y"])
        mode = scenario["mode"]
        note = scenario.get("note", "").strip()
        image_name = scenario.get("image_name", "").strip()

        lines.append(f"; {name}")
        if image_name:
            lines.append(f"; Reference Capture: {image_name}")
        if window_title:
            lines.append(f"; Target Window: {window_title}")
        if note:
            lines.append(f"; Note: {note}")
        lines.append(f"{hotkey}::{{")

        if sleep_before > 0:
            lines.append(f"    Sleep {sleep_before}")

        if window_title:
            lines.append(f"    if {build_winexist_expr(window_title, window_text)} {{")
            lines.append(f"        {build_winactivate_line(window_title, window_text)}")
            lines.append(f"        {build_winwaitactive_line(window_title, window_text, activation_timeout)}")
            if sleep_after_activate > 0:
                lines.append(f"        Sleep {sleep_after_activate}")
            indent = "        "
        else:
            indent = "    "

        lines.append(f"{indent}MouseMove {x}, {y}, {mouse_speed}")
        if sleep_after_move > 0:
            lines.append(f"{indent}Sleep {sleep_after_move}")

        if mode == "Move + Click":
            lines.append(f"{indent}Click")
        elif mode == "Move + Double Click":
            lines.append(f"{indent}Click 2")
        elif mode == "Move + Right Click":
            lines.append(f'{indent}Click "Right"')

        if window_title:
            lines.append("    } else {")
            lines.append(f'        MsgBox "대상 창을 찾지 못했습니다: {window_title}"')
            lines.append("    }")

        lines.append("}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


init_state()

st.title("PointKey MVP v3")
st.subheader("시나리오별 캡처-포인트-단축키 AHK 생성기")
st.caption("streamlit_image_coordinates 의존성을 제거한 버전입니다. 캡처 이미지를 보면서 X/Y를 조정하면 미리보기 이미지에 포인트가 표시됩니다.")

with st.sidebar:
    st.markdown("### 공통 설정")
    new_count = st.number_input("시나리오 개수", min_value=1, max_value=MAX_SCENARIOS, value=st.session_state.scenario_count, step=1)
    if new_count != st.session_state.scenario_count:
        resize_scenarios(int(new_count))
        st.rerun()

    st.session_state.coord_mode = st.selectbox(
        "좌표 기준",
        options=COORD_OPTIONS,
        index=COORD_OPTIONS.index(st.session_state.coord_mode),
        help="Window/Client를 추천합니다. Screen은 절대좌표입니다.",
    )
    st.session_state.mouse_speed = st.slider("마우스 이동 속도", 0, 100, st.session_state.mouse_speed, help="0이면 즉시 이동")
    st.session_state.sleep_before = st.number_input("실행 전 대기(ms)", min_value=0, max_value=5000, value=st.session_state.sleep_before, step=50)
    st.session_state.sleep_after_activate = st.number_input("창 활성화 후 대기(ms)", min_value=0, max_value=5000, value=st.session_state.sleep_after_activate, step=50)
    st.session_state.sleep_after_move = st.number_input("이동 후 대기(ms)", min_value=0, max_value=5000, value=st.session_state.sleep_after_move, step=50)
    st.session_state.activation_timeout = st.number_input("창 활성화 대기 타임아웃(초)", min_value=0.1, max_value=10.0, value=float(st.session_state.activation_timeout), step=0.1)

st.write("각 시나리오에서 캡처 이미지를 올리고 창 제목과 단축키를 지정한 뒤, 포인트를 맞춰 주세요.")

for i in range(st.session_state.scenario_count):
    scenario = st.session_state.scenarios[i]
    with st.expander(f"{scenario['name']} 설정", expanded=True if i < 2 else False):
        left, right = st.columns([1.1, 1])

        with left:
            uploaded = st.file_uploader(
                f"{scenario['name']} 참고용 화면 캡처 업로드",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"uploader_{i}",
                help="창 이름이 보이게 캡처해 두면 window title 입력에 도움이 됩니다.",
            )

            image = load_image(uploaded)
            if image is not None:
                w, h = image.size
                scenario["img_w"] = w
                scenario["img_h"] = h
                scenario["image_name"] = uploaded.name
                scenario["x"] = max(0, min(int(scenario["x"]), w - 1))
                scenario["y"] = max(0, min(int(scenario["y"]), h - 1))
                preview = draw_crosshair(image, scenario["x"], scenario["y"])
                st.image(preview, caption=f"{uploaded.name} | {w} x {h} | 현재 포인트: ({scenario['x']}, {scenario['y']})", use_container_width=True)
            else:
                st.info("캡처 이미지를 업로드하면 포인트 미리보기가 보입니다.")

        with right:
            scenario["name"] = st.text_input("시나리오 이름", value=scenario["name"], key=f"name_{i}")
            scenario["window_title"] = st.text_input(
                "대상 창 제목 (WinTitle)",
                value=scenario["window_title"],
                key=f"window_title_{i}",
                help="예: 메모장, Chrome, ERP Main Window",
            )
            scenario["window_text"] = st.text_input(
                "창 내부 텍스트 (선택)",
                value=scenario.get("window_text", ""),
                key=f"window_text_{i}",
                help="같은 제목 창이 여러 개일 때 보조 식별용",
            )
            scenario["hotkey"] = st.text_input("단축키", value=scenario["hotkey"], key=f"hotkey_{i}")
            scenario["mode"] = st.selectbox("동작", MODES, index=MODES.index(scenario["mode"]), key=f"mode_{i}")
            scenario["note"] = st.text_area("메모", value=scenario.get("note", ""), key=f"note_{i}", height=80)

            if scenario.get("img_w", 0) > 0 and scenario.get("img_h", 0) > 0:
                st.markdown("#### 포인트 지정")
                st.caption("이미지를 직접 클릭하는 방식 대신, 좌표를 조정하면 왼쪽 미리보기에 빨간 포인트가 표시됩니다.")
                scenario["x"] = st.slider(
                    "X 좌표",
                    min_value=0,
                    max_value=max(0, int(scenario["img_w"]) - 1),
                    value=min(int(scenario["x"]), max(0, int(scenario["img_w"]) - 1)),
                    key=f"x_slider_{i}",
                )
                scenario["y"] = st.slider(
                    "Y 좌표",
                    min_value=0,
                    max_value=max(0, int(scenario["img_h"]) - 1),
                    value=min(int(scenario["y"]), max(0, int(scenario["img_h"]) - 1)),
                    key=f"y_slider_{i}",
                )
                c1, c2 = st.columns(2)
                with c1:
                    scenario["x"] = st.number_input("X 직접입력", min_value=0, max_value=max(0, int(scenario["img_w"]) - 1), value=int(scenario["x"]), step=1, key=f"x_input_{i}")
                with c2:
                    scenario["y"] = st.number_input("Y 직접입력", min_value=0, max_value=max(0, int(scenario["img_h"]) - 1), value=int(scenario["y"]), step=1, key=f"y_input_{i}")
            else:
                st.warning("포인트를 지정하려면 먼저 캡처 이미지를 올려 주세요.")

ahk_code = generate_ahk(
    st.session_state.scenarios,
    st.session_state.coord_mode,
    st.session_state.mouse_speed,
    st.session_state.sleep_before,
    st.session_state.sleep_after_activate,
    st.session_state.sleep_after_move,
    float(st.session_state.activation_timeout),
)

st.markdown("---")
st.subheader("생성된 AutoHotkey v2 코드")
st.code(ahk_code, language="autohotkey")
st.download_button(
    label=".ahk 파일 다운로드",
    data=ahk_code.encode("utf-8"),
    file_name="pointkey_scenarios_v3.ahk",
    mime="text/plain",
)
