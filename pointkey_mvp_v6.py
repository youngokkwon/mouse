
import streamlit as st
from PIL import Image, ImageDraw
from io import BytesIO
from copy import deepcopy

st.set_page_config(page_title="PointKey MVP v6", layout="wide")

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
        "nudge_step": 10,
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
        "nudge_step": 10,
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
        "nudge_step": 10,
    },
]

MODES = ["Move Only", "Move + Click", "Move + Double Click", "Move + Right Click"]
COORD_OPTIONS = ["Window", "Client", "Screen"]
STEP_OPTIONS = [1, 5, 10, 20, 50]


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
            "nudge_step": 10,
        }
        items.append(base)
    return items


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


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
    sync_widget_state()


def sync_widget_state() -> None:
    for i, sc in enumerate(st.session_state.scenarios):
        x_key = f"x_direct_{i}"
        y_key = f"y_direct_{i}"
        step_key = f"step_{i}"
        if x_key not in st.session_state:
            st.session_state[x_key] = int(sc["x"])
        if y_key not in st.session_state:
            st.session_state[y_key] = int(sc["y"])
        if step_key not in st.session_state:
            st.session_state[step_key] = int(sc.get("nudge_step", 10))


def resize_scenarios(new_count: int) -> None:
    current = st.session_state.scenarios
    if new_count > len(current):
        current.extend(get_default_scenarios(new_count)[len(current):new_count])
    else:
        current = current[:new_count]
    st.session_state.scenarios = current
    st.session_state.scenario_count = new_count
    sync_widget_state()


def load_image(uploaded_file):
    if uploaded_file is None:
        return None
    return Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")


def draw_crosshair(image: Image.Image, x: int, y: int) -> Image.Image:
    img = image.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    x = clamp(x, 0, max(0, w - 1))
    y = clamp(y, 0, max(0, h - 1))
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


def build_click_lines(mode: str) -> list[str]:
    if mode == "Move Only":
        return []
    if mode == "Move + Click":
        return ["    Click"]
    if mode == "Move + Double Click":
        return ["    Click 2"]
    if mode == "Move + Right Click":
        return ['    Click "right"']
    return ["    Click"]


def generate_ahk_code() -> str:
    coord_mode = st.session_state.coord_mode
    mouse_speed = st.session_state.mouse_speed
    sleep_before = st.session_state.sleep_before
    sleep_after_activate = st.session_state.sleep_after_activate
    sleep_after_move = st.session_state.sleep_after_move
    timeout_ms = int(float(st.session_state.activation_timeout) * 1000)

    lines = [
        "#Requires AutoHotkey v2.0",
        f'CoordMode "Mouse", "{coord_mode}"',
        "",
    ]

    for sc in st.session_state.scenarios:
        hotkey = (sc["hotkey"] or "").strip()
        if not hotkey:
            continue

        window_title = (sc["window_title"] or "").strip()
        window_text = (sc["window_text"] or "").strip()
        x = int(sc["x"])
        y = int(sc["y"])
        mode = sc["mode"]
        note = (sc["note"] or "").strip()

        lines.append(f"{hotkey}::{{")
        if note:
            for note_line in note.splitlines():
                lines.append(f"    ; {note_line}")

        if sleep_before > 0:
            lines.append(f"    Sleep {sleep_before}")

        if window_title:
            winexist_expr = build_winexist_expr(window_title, window_text)
            lines.append(f"    hwnd := {winexist_expr}")
            lines.append("    if !hwnd {")
            lines.append('        MsgBox "대상 창을 찾지 못했습니다."')
            lines.append("        return")
            lines.append("    }")
            lines.append(f"    {build_winactivate_line(window_title, window_text)}")
            lines.append(f"    WinWaitActive hwnd,, {timeout_ms}")
            if sleep_after_activate > 0:
                lines.append(f"    Sleep {sleep_after_activate}")

        lines.append(f"    MouseMove {x}, {y}, {mouse_speed}")
        if sleep_after_move > 0:
            lines.append(f"    Sleep {sleep_after_move}")
        lines.extend(build_click_lines(mode))
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def sync_widget_coords(i: int) -> None:
    sc = st.session_state.scenarios[i]
    st.session_state[f"x_direct_{i}"] = int(sc["x"])
    st.session_state[f"y_direct_{i}"] = int(sc["y"])


def update_from_direct_inputs(i: int) -> None:
    sc = st.session_state.scenarios[i]
    x = int(st.session_state.get(f"x_direct_{i}", sc["x"]))
    y = int(st.session_state.get(f"y_direct_{i}", sc["y"]))

    if sc.get("img_w", 0) > 0:
        x = clamp(x, 0, int(sc["img_w"]) - 1)
    else:
        x = max(0, x)

    if sc.get("img_h", 0) > 0:
        y = clamp(y, 0, int(sc["img_h"]) - 1)
    else:
        y = max(0, y)

    sc["x"] = x
    sc["y"] = y
    sync_widget_coords(i)


def reset_point(i: int) -> None:
    sc = st.session_state.scenarios[i]
    sc["x"] = 0
    sc["y"] = 0
    sync_widget_coords(i)


def nudge_point(i: int, dx: int, dy: int) -> None:
    sc = st.session_state.scenarios[i]
    step = int(st.session_state.get(f"step_{i}", sc.get("nudge_step", 10)))
    sc["nudge_step"] = step

    max_x = max(0, int(sc.get("img_w", 0)) - 1)
    max_y = max(0, int(sc.get("img_h", 0)) - 1)

    new_x = int(sc["x"]) + dx * step
    new_y = int(sc["y"]) + dy * step

    if sc.get("img_w", 0) > 0:
        new_x = clamp(new_x, 0, max_x)
    else:
        new_x = max(0, new_x)

    if sc.get("img_h", 0) > 0:
        new_y = clamp(new_y, 0, max_y)
    else:
        new_y = max(0, new_y)

    sc["x"] = new_x
    sc["y"] = new_y
    sync_widget_coords(i)


def joystick_controls(i: int) -> None:
    sc = st.session_state.scenarios[i]

    st.markdown("#### 조이스틱 포인터")
    st.select_slider(
        "이동 단위(px)",
        options=STEP_OPTIONS,
        key=f"step_{i}",
    )
    sc["nudge_step"] = int(st.session_state.get(f"step_{i}", sc.get("nudge_step", 10)))

    row1 = st.columns(3)
    with row1[0]:
        st.button("↖", key=f"nw_{i}", use_container_width=True, on_click=nudge_point, args=(i, -1, -1))
    with row1[1]:
        st.button("↑", key=f"n_{i}", use_container_width=True, on_click=nudge_point, args=(i, 0, -1))
    with row1[2]:
        st.button("↗", key=f"ne_{i}", use_container_width=True, on_click=nudge_point, args=(i, 1, -1))

    row2 = st.columns(3)
    with row2[0]:
        st.button("←", key=f"w_{i}", use_container_width=True, on_click=nudge_point, args=(i, -1, 0))
    with row2[1]:
        st.button("● Reset", key=f"reset_{i}", use_container_width=True, on_click=reset_point, args=(i,))
    with row2[2]:
        st.button("→", key=f"e_{i}", use_container_width=True, on_click=nudge_point, args=(i, 1, 0))

    row3 = st.columns(3)
    with row3[0]:
        st.button("↙", key=f"sw_{i}", use_container_width=True, on_click=nudge_point, args=(i, -1, 1))
    with row3[1]:
        st.button("↓", key=f"s_{i}", use_container_width=True, on_click=nudge_point, args=(i, 0, 1))
    with row3[2]:
        st.button("↘", key=f"se_{i}", use_container_width=True, on_click=nudge_point, args=(i, 1, 1))


init_state()

st.title("PointKey MVP v6")
st.caption("시나리오별 캡처 이미지 + 창 제목 + 조이스틱형 포인터 이동 + AHK v2 코드 생성기")

with st.sidebar:
    st.header("전역 설정")
    scenario_count = st.number_input("시나리오 개수", min_value=1, max_value=MAX_SCENARIOS, value=st.session_state.scenario_count, step=1)
    if scenario_count != st.session_state.scenario_count:
        resize_scenarios(int(scenario_count))

    st.selectbox("좌표 기준 (CoordMode)", COORD_OPTIONS, index=COORD_OPTIONS.index(st.session_state.coord_mode), key="coord_mode")
    st.slider("마우스 이동 속도", 0, 100, key="mouse_speed")
    st.number_input("실행 전 대기(ms)", min_value=0, max_value=5000, step=10, key="sleep_before")
    st.number_input("창 활성화 후 대기(ms)", min_value=0, max_value=5000, step=10, key="sleep_after_activate")
    st.number_input("마우스 이동 후 대기(ms)", min_value=0, max_value=5000, step=10, key="sleep_after_move")
    st.number_input("창 활성화 타임아웃(초)", min_value=0.1, max_value=10.0, step=0.1, key="activation_timeout")

for i, sc in enumerate(st.session_state.scenarios):
    st.markdown("---")
    st.subheader(sc["name"])

    left, right = st.columns([1.25, 1])

    with right:
        sc["window_title"] = st.text_input("대상 창 제목 (WinTitle)", value=sc["window_title"], key=f"window_title_{i}")
        sc["window_text"] = st.text_input("창 내부 텍스트 (선택)", value=sc["window_text"], key=f"window_text_{i}")
        sc["hotkey"] = st.text_input("단축키", value=sc["hotkey"], key=f"hotkey_{i}")
        sc["mode"] = st.selectbox("동작", MODES, index=MODES.index(sc["mode"]) if sc["mode"] in MODES else 1, key=f"mode_{i}")
        sc["note"] = st.text_area("메모", value=sc["note"], key=f"note_{i}", height=90)

        st.markdown("#### 좌표 직접 입력")
        input_cols = st.columns(2)
        with input_cols[0]:
            st.number_input(
                "X 좌표",
                min_value=0,
                max_value=max(0, int(sc["img_w"]) - 1) if sc["img_w"] else 10000,
                step=1,
                key=f"x_direct_{i}",
                on_change=update_from_direct_inputs,
                args=(i,),
            )
        with input_cols[1]:
            st.number_input(
                "Y 좌표",
                min_value=0,
                max_value=max(0, int(sc["img_h"]) - 1) if sc["img_h"] else 10000,
                step=1,
                key=f"y_direct_{i}",
                on_change=update_from_direct_inputs,
                args=(i,),
            )

        joystick_controls(i)
        st.caption(f"현재 좌표: ({sc['x']}, {sc['y']})")

    with left:
        uploaded = st.file_uploader(
            f"{sc['name']} 참고용 화면 캡처 업로드",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"uploader_{i}",
        )

        image = load_image(uploaded)
        if image is not None:
            sc["image_name"] = uploaded.name
            sc["img_w"], sc["img_h"] = image.size
            sc["x"] = clamp(int(sc["x"]), 0, image.size[0] - 1)
            sc["y"] = clamp(int(sc["y"]), 0, image.size[1] - 1)
            sync_widget_coords(i)
            preview = draw_crosshair(image, int(sc["x"]), int(sc["y"]))
            st.image(
                preview,
                caption=f"{sc['image_name']} | {sc['img_w']} x {sc['img_h']} | 포인트: ({sc['x']}, {sc['y']})",
                use_container_width=True
            )
        else:
            sc["image_name"] = ""
            sc["img_w"], sc["img_h"] = 0, 0
            st.info("참고용 화면 캡처를 업로드하면 현재 포인트를 빨간 십자로 표시합니다.")

st.markdown("---")
st.subheader("생성된 AutoHotkey v2 코드")
code_text = generate_ahk_code()
st.code(code_text, language="ahk")

st.download_button(
    label=".ahk 파일 다운로드",
    data=code_text.encode("utf-8"),
    file_name="pointkey_generated_v6.ahk",
    mime="text/plain",
)
