import streamlit as st
from PIL import Image
from io import BytesIO
from textwrap import dedent

st.set_page_config(page_title="PointKey MVP", layout="wide")

DEFAULT_ACTIONS = [
    {"name": "Action 1", "hotkey": "F1", "x": 100, "y": 100, "mode": "Move + Click", "note": ""},
    {"name": "Action 2", "hotkey": "F2", "x": 200, "y": 200, "mode": "Move + Click", "note": ""},
    {"name": "Action 3", "hotkey": "F3", "x": 300, "y": 300, "mode": "Move + Click", "note": ""},
]


def init_state() -> None:
    if "actions" not in st.session_state:
        st.session_state.actions = DEFAULT_ACTIONS.copy()
    if "coord_mode" not in st.session_state:
        st.session_state.coord_mode = "Screen"
    if "mouse_speed" not in st.session_state:
        st.session_state.mouse_speed = 0
    if "sleep_before" not in st.session_state:
        st.session_state.sleep_before = 0
    if "sleep_after_move" not in st.session_state:
        st.session_state.sleep_after_move = 0


def generate_ahk(actions, coord_mode: str, mouse_speed: int, sleep_before: int, sleep_after_move: int) -> str:
    lines = [
        "#Requires AutoHotkey v2.0",
        f'CoordMode "Mouse", "{coord_mode}"',
        "",
    ]

    for action in actions:
        hotkey = action["hotkey"].strip()
        if not hotkey:
            continue
        name = action["name"].strip() or "Unnamed Action"
        x = int(action["x"])
        y = int(action["y"])
        mode = action["mode"]
        note = action.get("note", "").strip()

        lines.append(f"; {name}")
        if note:
            lines.append(f"; Note: {note}")
        lines.append(f"{hotkey}::{{")
        if sleep_before > 0:
            lines.append(f"    Sleep {sleep_before}")
        lines.append(f"    MouseMove {x}, {y}, {mouse_speed}")
        if sleep_after_move > 0:
            lines.append(f"    Sleep {sleep_after_move}")

        if mode == "Move Only":
            pass
        elif mode == "Move + Click":
            lines.append("    Click")
        elif mode == "Move + Double Click":
            lines.append("    Click 2")
        elif mode == "Move + Right Click":
            lines.append("    Click \"Right\"")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_uploaded_image(uploaded_file):
    if uploaded_file is None:
        st.info("참고용 화면 캡처를 업로드하면 여기에서 미리 볼 수 있어요.")
        return None

    image_bytes = uploaded_file.read()
    image = Image.open(BytesIO(image_bytes))
    st.image(image, caption=f"업로드된 캡처본 · {image.width} x {image.height}", use_container_width=True)
    st.caption("이 MVP는 이미지 위 클릭 좌표 추출 기능은 아직 없고, X/Y를 수동 입력하는 버전입니다.")
    return image


init_state()

st.title("PointKey MVP")
st.subheader("스크린샷 기반 AHK 단축키 생성기")
st.write("참고용 화면 캡처를 보고, 목적지 좌표와 단축키를 입력하면 AutoHotkey v2 코드를 생성합니다.")

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### 1) 참고용 화면 캡처")
    uploaded = st.file_uploader("PNG / JPG 업로드", type=["png", "jpg", "jpeg"])
    uploaded_image = render_uploaded_image(uploaded)

with right:
    st.markdown("### 2) 공통 설정")
    st.session_state.coord_mode = st.selectbox(
        "좌표 기준",
        options=["Screen", "Window", "Client"],
        index=["Screen", "Window", "Client"].index(st.session_state.coord_mode),
        help="Screen은 절대좌표, Window/Client는 활성 창 기준 상대좌표입니다.",
    )
    st.session_state.mouse_speed = st.slider("마우스 이동 속도", 0, 100, st.session_state.mouse_speed, help="0이면 즉시 이동")
    st.session_state.sleep_before = st.number_input("실행 전 대기(ms)", min_value=0, max_value=5000, value=st.session_state.sleep_before, step=50)
    st.session_state.sleep_after_move = st.number_input("이동 후 대기(ms)", min_value=0, max_value=5000, value=st.session_state.sleep_after_move, step=50)

    if uploaded_image:
        st.markdown("### 3) 캡처본 정보")
        st.write(f"가로: **{uploaded_image.width}px**")
        st.write(f"세로: **{uploaded_image.height}px**")
        st.caption("이미지 크기를 기준으로 목적지 좌표를 확인해 넣으면 됩니다.")

st.markdown("---")
st.markdown("### 4) 액션 3개 등록")

modes = ["Move Only", "Move + Click", "Move + Double Click", "Move + Right Click"]

for i in range(3):
    action = st.session_state.actions[i]
    st.markdown(f"#### Action {i+1}")
    c1, c2, c3, c4, c5 = st.columns([1.3, 1, 1, 1, 1.3])
    with c1:
        action["name"] = st.text_input(f"액션 이름 {i+1}", value=action["name"], key=f"name_{i}")
    with c2:
        action["hotkey"] = st.text_input(f"단축키 {i+1}", value=action["hotkey"], key=f"hotkey_{i}")
    with c3:
        action["x"] = st.number_input(f"X {i+1}", min_value=0, value=int(action["x"]), step=1, key=f"x_{i}")
    with c4:
        action["y"] = st.number_input(f"Y {i+1}", min_value=0, value=int(action["y"]), step=1, key=f"y_{i}")
    with c5:
        current_mode_index = modes.index(action["mode"]) if action["mode"] in modes else 1
        action["mode"] = st.selectbox(f"동작 {i+1}", modes, index=current_mode_index, key=f"mode_{i}")

    action["note"] = st.text_input(f"메모 {i+1}", value=action.get("note", ""), key=f"note_{i}")
    st.session_state.actions[i] = action

st.markdown("---")
code = generate_ahk(
    st.session_state.actions,
    st.session_state.coord_mode,
    int(st.session_state.mouse_speed),
    int(st.session_state.sleep_before),
    int(st.session_state.sleep_after_move),
)

st.markdown("### 5) 생성된 AutoHotkey v2 코드")
st.code(code, language="autohotkey")

col_a, col_b = st.columns([1, 1])
with col_a:
    st.download_button(
        label=".ahk 파일 다운로드",
        data=code,
        file_name="pointkey_generated.ahk",
        mime="text/plain",
        use_container_width=True,
    )
with col_b:
    if st.button("기본값으로 초기화", use_container_width=True):
        st.session_state.actions = DEFAULT_ACTIONS.copy()
        st.session_state.coord_mode = "Screen"
        st.session_state.mouse_speed = 0
        st.session_state.sleep_before = 0
        st.session_state.sleep_after_move = 0
        st.rerun()

st.markdown("---")
st.markdown("### 다음 단계 아이디어")
st.write(
    dedent(
        """
        - 업로드한 이미지 위를 직접 클릭해서 X/Y 자동 채우기
        - 버튼 PNG를 넣으면 ImageSearch 코드 생성
        - 여러 액션을 한 시나리오로 순차 실행
        - 창 제목/프로세스명 조건 추가
        """
    ).strip()
)
