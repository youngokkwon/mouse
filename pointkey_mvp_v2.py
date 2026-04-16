import streamlit as st
from PIL import Image
from io import BytesIO
from textwrap import dedent
from copy import deepcopy
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PointKey MVP v2", layout="wide")

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
    return Image.open(BytesIO(uploaded_file.getvalue()))


def render_clickable_image(image, scenario_idx: int):
    click_value = streamlit_image_coordinates(
        image,
        key=f"imgcoord_{scenario_idx}",
        use_column_width=True,
    )
    if click_value:
        st.session_state.scenarios[scenario_idx]["x"] = int(click_value["x"])
        st.session_state.scenarios[scenario_idx]["y"] = int(click_value["y"])
        st.success(f"포인트 저장됨 → X={click_value['x']}, Y={click_value['y']}")
        st.caption("업로드한 캡처 이미지를 클릭하면 마지막 클릭 좌표가 저장됩니다.")


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

        lines.append(f"; {name}")
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

        if mode == "Move Only":
            pass
        elif mode == "Move + Click":
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

st.title("PointKey MVP v2")
st.subheader("시나리오별 캡처-포인트-단축키 AHK 생성기")
st.write("각 시나리오마다 화면 캡처를 올리고, 이미지 위에서 목적지 포인트를 클릭한 뒤, 해당 시나리오용 단축키를 지정합니다.")

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
    st.session_state.activation_timeout = st.number_input("창 활성화 대기 타임아웃(초)", min_value=0.5, max_value=10.0, value=float(st.session_state.activation_timeout), step=0.5)

    if st.button("기본값으로 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("---")
st.markdown("### 시나리오 설정")

for i in range(st.session_state.scenario_count):
    scenario = st.session_state.scenarios[i]
    st.markdown(f"## {scenario['name']}")

    left, right = st.columns([1.15, 1])

    with left:
        uploaded = st.file_uploader(
            f"{scenario['name']} 참고용 화면 캡처 업로드",
            type=["png", "jpg", "jpeg"],
            key=f"upload_{i}",
            help="창 이름이 상단에 보이는 캡처를 권장합니다.",
        )
        image = load_image(uploaded)
        if image is not None:
            st.caption(f"캡처 크기: {image.width} x {image.height}")
            render_clickable_image(image, i)
        else:
            st.info("캡처 이미지를 올리면, 이미지 위를 클릭해서 해당 시나리오의 목적지 포인트를 저장할 수 있어요.")

    with right:
        scenario["name"] = st.text_input("시나리오 이름", value=scenario["name"], key=f"scenario_name_{i}")
        scenario["window_title"] = st.text_input(
            "대상 창 제목 (WinTitle)",
            value=scenario["window_title"],
            key=f"window_title_{i}",
            help="예: 메모장, Chrome, 업무시스템 화면 제목 일부",
        )
        scenario["window_text"] = st.text_input(
            "보조 식별 텍스트 (선택)",
            value=scenario.get("window_text", ""),
            key=f"window_text_{i}",
            help="필요할 때만 사용합니다. 비워도 됩니다.",
        )
        scenario["hotkey"] = st.text_input("단축키", value=scenario["hotkey"], key=f"hotkey_{i}")
        scenario["mode"] = st.selectbox(
            "동작 유형",
            options=MODES,
            index=MODES.index(scenario["mode"]) if scenario["mode"] in MODES else 1,
            key=f"mode_{i}",
        )
        coords = st.columns(2)
        with coords[0]:
            scenario["x"] = st.number_input("X", min_value=0, value=int(scenario["x"]), step=1, key=f"x_{i}")
        with coords[1]:
            scenario["y"] = st.number_input("Y", min_value=0, value=int(scenario["y"]), step=1, key=f"y_{i}")
        scenario["note"] = st.text_input("메모", value=scenario.get("note", ""), key=f"note_{i}")

        st.caption(
            "흐름 예시: 시나리오 1 화면 → 단축키 1, 시나리오 2 화면 → 단축키 2.\n"
            "같은 창 안 좌표라면 Window 또는 Client 기준을 추천합니다."
        )

    st.session_state.scenarios[i] = scenario
    st.markdown("---")

code = generate_ahk(
    st.session_state.scenarios,
    st.session_state.coord_mode,
    int(st.session_state.mouse_speed),
    int(st.session_state.sleep_before),
    int(st.session_state.sleep_after_activate),
    int(st.session_state.sleep_after_move),
    float(st.session_state.activation_timeout),
)

st.markdown("### 생성된 AutoHotkey v2 코드")
st.code(code, language="autohotkey")

st.download_button(
    label=".ahk 파일 다운로드",
    data=code,
    file_name="pointkey_scenarios_generated.ahk",
    mime="text/plain",
    use_container_width=True,
)

st.markdown("---")
st.markdown("### 사용 메모")
st.write(
    dedent(
        """
        - 각 시나리오는 **캡처 이미지 + 창 제목 + 포인트 좌표 + 단축키** 한 세트입니다.
        - 업로드한 이미지를 클릭하면 해당 시나리오의 X/Y가 바로 저장됩니다.
        - AHK 코드는 먼저 대상 창을 찾고 활성화한 뒤, 저장한 포인트로 이동해 액션을 실행합니다.
        - `Window` 기준은 창 바깥 프레임까지 포함하고, `Client` 기준은 창 내부 작업영역 기준입니다.
        """
    ).strip()
)
