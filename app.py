import streamlit as st
import pandas as pd
import plotly.express as px
import ast
import os
import hmac

st.set_page_config(page_title="ImplantLab", page_icon="🧬", layout="wide")

# --- Visual identity: retain the original ImplantLab dark blue / cyan UI ---
st.markdown('''
<style>
.stApp {background:linear-gradient(140deg,#0b1220,#10263a);color:#e8f2ff}
[data-testid="stSidebar"]{background:#0a1422}
.block-container{max-width:1200px;padding-top:1.7rem}
.hero{padding:2rem;border:1px solid #31516c;border-radius:20px;background:linear-gradient(120deg,#15334b,#101d31)}
.kicker{color:#67e8f9;text-transform:uppercase;font-size:.78rem;font-weight:800;letter-spacing:.15em}
.panel{background:#122238;border:1px solid #2b435d;border-radius:14px;padding:1rem}
.subtle{color:#afc1d7}
.sarah{background:linear-gradient(120deg,#193b55,#17283e);border:1px solid #39718a;border-left:5px solid #67e8f9;border-radius:14px;padding:1rem 1.2rem;margin:.5rem 0 1rem 0}
div.stButton>button{border-radius:10px;border:1px solid #39718a}
</style>
''', unsafe_allow_html=True)

MODULES = [
    "01 · Register Samples", "02 · Mechanical Performance", "03 · Cell Viability",
    "04 · Candidate Materials", "05 · Independent Research Challenge", "BONUS · Semiconductor Lab"
]

# --- Persistent-in-session game state ---
DEFAULTS = {"score": 50, "unlocked": 6, "done": set(), "correct": set(), "wrong": set(),
            "attempted": set(), "Sarah": 0, "xp_correct": 10, "xp_penalty": 5,
            "admin_authenticated": False}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, set) else value


def sarah(level=None, message=None):
    level = st.session_state.Sarah if level is None else level
    stages = [
        ("Sarah · Lab Trainee", "👩🏻‍🔬", "Hi! I’m Sarah. I’m new to Python too, so let’s learn by running a few tiny lab experiments."),
        ("Sarah · Sample Analyst", "🧪", "I can now register samples and keep their measurements organised. Let’s test the numbers!"),
        ("Sarah · Mechanical Tester", "⚙️", "I’ve learned to calculate stress and strain. I’m starting to understand how materials behave."),
        ("Sarah · Cell Data Analyst", "🧫", "Lists, loops and accumulation are in my toolkit now. I can analyse repeated cell readings!"),
        ("Sarah · Materials Engineer", "🦾", "I can compare multiple constraints and build reusable functions. Let’s make a defensible choice."),
        ("Sarah · Research Programmer", "🔬", "I can now investigate an unfamiliar dataset and explain the result with code."),
        ("Sarah · Python Semiconductor Engineer", "👩🏻‍💻", "Bonus mission complete! I can now help a semiconductor research team solve a manufacturing problem.")
    ]
    name, emoji, default = stages[min(level, 6)]
    st.markdown(f'<div class="sarah"><b>{emoji} {name}</b><br>{message or default}</div>', unsafe_allow_html=True)


def reset_campaign():
    st.session_state.score = 0
    st.session_state.unlocked = 6
    st.session_state.done = set()
    st.session_state.correct = set()
    st.session_state.wrong = set()
    st.session_state.attempted = set()
    st.session_state.Sarah = 0


def award(key, is_correct, explanation, points=None, penalty=None):
    """Score each exercise once; wrong answers cost points. A zero score resets the campaign."""
    points = st.session_state.xp_correct if points is None else points
    penalty = st.session_state.xp_penalty if penalty is None else penalty
    if key in st.session_state.correct:
        st.info("Already solved! You can move on to the next exercise.")
        return
    st.session_state.attempted.add(key)
    if is_correct:
        st.session_state.score += points
        st.session_state.correct.add(key)
        st.success(f"✅ Correct! +{points} points. {explanation}")
        sarah(message="That’s right! Nice work — I’m learning from your code decisions. ✨")
    else:
        st.session_state.score -= penalty
        st.session_state.wrong.add(key)
        st.error(f"Not quite. −{penalty} points. {explanation}")
        sarah(message="Oops, that result doesn’t match the lab logic. Read the hint, then try again in the next run. 💡")
    if st.session_state.score <= 0:
        st.error("Score reached zero. Sarah is sending the trainee back to Module 1 for a fresh run. Your campaign progress has been reset.")
        reset_campaign()
        st.rerun()


def mcq(key, prompt, options, answer, explanation, points=None, penalty=None):
    st.markdown(f"**{prompt}**")
    choice = st.radio("Choose one", options, key=f"{key}_choice", label_visibility="collapsed")
    if st.button("Submit answer", key=f"{key}_submit", disabled=key in st.session_state.correct):
        award(key, choice == answer, explanation, points, penalty)


def fill_blank(key, prompt, expected, explanation, placeholder="Type the missing Python code"):
    st.markdown(f"**{prompt}**")
    answer = st.text_input("Code blank", key=f"{key}_input", placeholder=placeholder)
    if st.button("Check code", key=f"{key}_check", disabled=key in st.session_state.correct):
        normalized = answer.strip().replace(" ", "")
        valid = {x.replace(" ", "") for x in (expected if isinstance(expected, tuple) else (expected,))}
        award(key, normalized in valid, explanation)



def header(num, title, subtitle):
    st.markdown(f'<div class="kicker">{num}</div><h1>{title}</h1><p class="subtle">{subtitle}</p>', unsafe_allow_html=True)


def module_complete(number, keys, extra_ok=True):
    all_ok = all(k in st.session_state.correct for k in keys) and extra_ok
    if all_ok:
        if number not in st.session_state.done:
            st.session_state.done.add(number)
            st.session_state.Sarah = max(st.session_state.Sarah, number)
        st.success(f"MODULE {number} COMPLETE · Great work!")
        sarah()
    else:
        missing = sum(k not in st.session_state.correct for k in keys)
        st.info(f"Keep practising — {missing} scored exercise(s) remain in this module. All modules remain available.")

# --- Sidebar and open navigation ---
with st.sidebar:
    st.title("🧬 ImplantLab")
    st.caption("Python × Materials Science × Biomedical Research")
    st.metric("Game score", f"{st.session_state.score} XP")
    st.progress(min(st.session_state.score / 150, 1.0), text="Score meter")
    st.metric("Modules completed", f"{len(st.session_state.done)}/6")
    st.progress(len(st.session_state.done) / 6)
    st.caption("Correct: +10 XP  ·  Incorrect: −5 XP")
    st.divider()
    available = ["Home"] + MODULES + ["Research Sandbox"]

    with st.expander("🔐 Admin access"):
        if not st.session_state.admin_authenticated:
            admin_entry = st.text_input("Admin password", type="password", key="admin_password_entry")
            if st.button("Unlock admin mode", key="admin_login"):
                configured_password = st.secrets.get(
                    "admin_password",
                    os.getenv("IMPLANTLAB_ADMIN_PASSWORD", "sarahadmin2026")
                )
                if hmac.compare_digest(admin_entry, str(configured_password)):
                    st.session_state.admin_authenticated = True
                    st.success("Admin mode enabled.")
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")
        else:
            st.success("Admin mode is active.")
            if st.button("Log out of admin mode", key="admin_logout"):
                st.session_state.admin_authenticated = False
                st.rerun()

    if st.session_state.admin_authenticated:
        available.append("🛠 Admin Panel")
    page = st.radio("Research pathway", available)
    st.divider()
    st.caption("All datasets and outcomes are fictional demonstrations. Not for clinical or manufacturing decisions.")

if page == "Home":
    header("VIRTUAL RESEARCH TRAINING", "Design safer implants. Learn Python by doing.", "A mission-based Python learning lab where every concept is connected to a materials-science problem.")
    sarah()
    a,b,c = st.columns(3)
    a.metric("Learning modules", "5 + bonus")
    b.metric("Current score", f"{st.session_state.score} XP")
    c.metric("Sarah’s level", f"{st.session_state.Sarah}/6")
    st.subheader("Your research pathway")
    for i, title in enumerate(MODULES, start=1):
        status = "✅ Complete" if i in st.session_state.done else "🔓 Available"
        st.markdown(f'<div class="panel"><b>{title}</b><br><span class="subtle">{status}</span></div>', unsafe_allow_html=True)
    st.info("Each module starts with theory, concepts and Python syntax, then moves to MCQs and code-snippet fill-in-the-blanks. All modules are open from the beginning — explore them in any order.")
    st.warning("The score is a learning mechanic. At zero, the score and learner progress reset, but every module remains accessible. Progress is held in the current Streamlit session.")

elif page == MODULES[0]:
    header("MISSION 01", "Register the samples", "Variables, Python data types, measurement records and arithmetic type changes.")
    sarah()
    st.subheader("Theory · What does a sample record contain?")
    st.write("A materials researcher records a sample identity and its measured quantities before analysis. A variable is a named reference to a value. Python assigns types dynamically, so arithmetic can produce a different type from the original variables.")
    st.markdown("**Core data types**")
    st.markdown("- `str`: sample labels such as `\"Ti-6Al-4V\"`\n- `int`: whole-number readings or counts, such as `450`\n- `float`: measured quantities with decimals, such as `2500.0`\n- `bool`: a logical state, `True` or `False`\n- `list`: a collection of repeated measurements")
    st.info("Type behaviour: `int + int` usually gives an int; `int / int` gives a float; `str + str` concatenates text; incompatible operations raise a TypeError.")
    st.subheader("Sample registration bench")
    a,b = st.columns(2)
    with a:
        name = st.selectbox("Sample", ["Ti-6Al-4V", "316L stainless steel", "HA-Ti composite", "Mg-Zn alloy"])
        force = st.number_input("Applied force (N)", 100.0, 10000.0, 2500.0, 100.0)
        area = st.number_input("Cross-sectional area (mm²)", 1.0, 100.0, 12.5, 0.5)
        strain = st.number_input("Measured strain (dimensionless)", 0.0001, 0.1, 0.0025, 0.0001, format="%.4f")
    with b:
        cost = st.number_input("Unit cost (₹)", 100, 100000, 4500, 100)
        reps = st.text_input("Replicate viability readings (%)", "88.6, 91.2, 89.7, 90.4")
        stress = force / area
        st.metric("Calculated stress", f"{stress:.2f} MPa")
        st.json({"sample": name, "force_N": force, "area_mm2": area, "strain": strain, "stress_MPa": round(stress,2), "cost_INR": cost})
        st.caption(f"Python types → name: {type(name).__name__}, force: {type(force).__name__}, cost: {type(cost).__name__}, viability list: list[str] before parsing.")
    st.subheader("Quick checks · data types")
    mcq("m1_str", "1. Which assignment creates a string?", ['A) sample = Ti-6Al-4V', 'B) sample = "Ti-6Al-4V"', 'C) sample = str Ti-6Al-4V'], 'B) sample = "Ti-6Al-4V"', "Text must be enclosed in matching quotation marks.")
    mcq("m1_int", "2. Which is an integer?", ["A) 450", 'B) "450"', "C) 450.0"], "A) 450", "An integer has no decimal part.")
    mcq("m1_float", "3. What is the type of 2500 / 2 in Python?", ["A) int", "B) float", "C) str"], "B) float", "The `/` operator performs true division and returns a float.")
    mcq("m1_bool", "4. Which is Python's Boolean false value?", ["A) false", 'B) "False"', "C) False"], "C) False", "Boolean keywords are capitalised in Python.")
    fill_blank("m1_type", "5. Fill the blank to inspect the type of stress_MPa: `print(____(stress_MPa))`", "type", "The type() function reports the object's data type.")
    fill_blank("m1_convert", "6. Fill the conversion function: `value = ____(reading)` where reading is the string 12.5.", "float", "float() converts numeric text into a floating-point number.")
    module_complete(1, ["m1_str","m1_int","m1_float","m1_bool","m1_type","m1_convert"])

elif page == MODULES[1]:
    header("MISSION 02", "Test mechanical performance", "Stress–strain data, Young’s modulus, arithmetic operators and conditional decisions.")
    sarah()
    st.subheader("Theory · From a test curve to a material property")
    st.write("In the linear-elastic region, Young’s modulus is the slope of the stress–strain curve. For a simplified two-point dataset, E = change in stress / change in strain. Since strain is dimensionless, stress in MPa gives E in MPa; divide by 1000 for GPa.")
    st.latex(r"E = \frac{\Delta \sigma}{\Delta \varepsilon} = \frac{\sigma_2-\sigma_1}{\varepsilon_2-\varepsilon_1}")
    st.write("Reference ranges below are broad illustrative teaching values, not material specifications. Real selection requires grade, processing, temperature, fatigue, corrosion and standards data.")
    refs = pd.DataFrame([
        {"Material family":"Ti-6Al-4V", "Reference E (GPa)":"105–120", "Typical context":"Load-bearing implant alloy"},
        {"Material family":"316L stainless steel", "Reference E (GPa)":"180–210", "Typical context":"Temporary/fixation devices"},
        {"Material family":"Cortical bone", "Reference E (GPa)":"7–30", "Typical context":"Biological comparison"},
        {"Material family":"Hydroxyapatite ceramic", "Reference E (GPa)":"70–120", "Typical context":"Bioactive brittle ceramic"},
        {"Material family":"PEEK", "Reference E (GPa)":"3–4", "Typical context":"Polymer implant component"},
    ])
    st.dataframe(refs, use_container_width=True, hide_index=True)
    st.subheader("Mechanical test console")
    a,b = st.columns(2)
    with a:
        material = st.selectbox("Candidate material", list(refs["Material family"]))
        s1 = st.number_input("Stress point 1 (MPa)", 0.0, 1000.0, 20.0, 1.0)
        e1 = st.number_input("Strain point 1", 0.0001, 0.2, 0.0002, 0.0001, format="%.4f")
        s2 = st.number_input("Stress point 2 (MPa)", 0.1, 2000.0, 120.0, 1.0)
        e2 = st.number_input("Strain point 2", 0.0002, 0.3, 0.0012, 0.0001, format="%.4f")
        e_min, e_max = st.slider("Illustrative acceptable modulus window (GPa)", 0.5, 220.0, (80.0, 130.0), 0.5)
    with b:
        modulus_mpa = (s2-s1)/(e2-e1) if e2 != e1 else None
        modulus_gpa = modulus_mpa/1000 if modulus_mpa is not None else None
        st.metric("Calculated Young's modulus", "Undefined" if modulus_gpa is None else f"{modulus_gpa:.2f} GPa")
        in_window = modulus_gpa is not None and e_min <= modulus_gpa <= e_max
        st.success("Within the selected teaching window") if in_window else st.warning("Outside the selected teaching window / check data")
        st.caption("A two-point slope is only meaningful if both points lie in the linear-elastic region.")
        curve = pd.DataFrame({"Strain":[e1,e2],"Stress (MPa)": [s1,s2]})
        st.plotly_chart(px.line(curve, x="Strain", y="Stress (MPa)", markers=True, title="Entered stress–strain points"), use_container_width=True)
    st.subheader("Python syntax · arithmetic and if/else")
    mcq("m2_op", "1. Which operator checks equality?", ["A) =", "B) ==", "C) !="], "B) ==", "A single = assigns; == compares.")
    mcq("m2_if", "2. Which keyword begins a conditional branch?", ["A) when", "B) if", "C) check"], "B) if", "if starts a conditional statement.")
    fill_blank("m2_delta", "3. Fill the operator: `E = (stress_2 - stress_1) ____ (strain_2 - strain_1)`", "/", "Young's modulus is the stress change divided by strain change.")
    fill_blank("m2_else", "4. Complete the branch: `____:` followed by the code for the other outcome", "else", "else handles the case when the if condition is false.")
    fill_blank("m2_modulus", "5. Fill the conversion: `E_GPa = E_MPa ____ 1000`", "/", "Divide MPa by 1000 to convert to GPa.")
    mcq("m2_range", "6. A calculated modulus is 100 GPa. Does it fall within the illustrative 80–130 GPa window?", ["A) Yes", "B) No", "C) Cannot tell"], "A) Yes", "100 lies between 80 and 130 GPa.")
    module_complete(2, ["m2_op","m2_if","m2_delta","m2_else","m2_modulus","m2_range"])

elif page == MODULES[2]:
    header("MISSION 03", "Analyse cell viability", "Cell structures, viability readings, lists, loops and accumulation.")
    sarah()
    st.subheader("Theory · What are we measuring?")
    st.write("A simplified cell-viability assay estimates the fraction of cells that remain metabolically active or intact after exposure. The cell membrane regulates exchange; the nucleus stores genetic information; mitochondria support cellular energy production. Assay values are screening signals, not proof of implant safety.")
    st.markdown("**Python concepts**")
    st.write("A list stores multiple readings. A `for` loop visits each reading. An accumulator adds values one by one; dividing the total by the number of readings gives the mean.")
    cell_data = {"Membrane integrity": [91.8, 89.6, 92.4, 90.7], "Metabolic activity": [86.4, 88.1, 84.9, 87.3], "Cell attachment": [90.2, 92.1, 89.4, 91.0]}
    a,b = st.columns(2)
    with a:
        assay = st.selectbox("Cell assay / structure indicator", list(cell_data))
        threshold = st.slider("Illustrative viability threshold (%)", 50, 100, 85)
        readings = cell_data[assay]
    with b:
        total = 0
        for value in readings:
            total += value
        average = total / len(readings)
        st.metric("Mean reading", f"{average:.1f}%")
        st.metric("Screen", "PASS" if average >= threshold else "REVIEW")
        st.dataframe(pd.DataFrame({"Replicate":range(1,5),"Reading (%)":readings}), hide_index=True, use_container_width=True)
    st.subheader("Quick checks · lists and loops")
    mcq("m3_list", "1. Which brackets create a Python list?", ["A) {}", "B) []", "C) ()"], "B) []", "Square brackets create a list.")
    mcq("m3_loop", "2. Which loop visits every item in viability?", ["A) for x in viability:", "B) if x in viability:", "C) repeat viability:"], "A) for x in viability:", "A for loop iterates through each list item.")
    fill_blank("m3_acc", "3. Fill the accumulation operator: `total ____ reading`", "+=", "The += operator adds the new reading to the running total.")
    fill_blank("m3_len", "4. Fill the function: `average = total / ____(viability)`", "len", "len() returns the number of readings.")
    mcq("m3_mean", "5. Four replicate readings are 86, 90, 92 and 88%. What is their mean?", ["A) 88%", "B) 89%", "C) 90%"], "B) 89%", "The sum is 356; 356 divided by 4 is 89.")
    fill_blank("m3_loopvar", "6. Complete the loop header: `for reading ____ readings:`", "in", "The in keyword iterates over items in a collection.")
    module_complete(3, ["m3_list","m3_loop","m3_acc","m3_len","m3_mean","m3_loopvar"])

elif page == MODULES[3]:
    header("MISSION 04", "Compare candidate materials", "Use dictionaries, tuples, functions, comparison operators and logical reasoning.")
    sarah()
    st.subheader("Theory · Multiple constraints, one decision")
    st.write("A dictionary stores named properties for each material. A tuple can hold a fixed reference range. A function packages a repeated calculation so it can be reused. The candidate passes only if mechanical, biological and budget conditions are all satisfied.")
    st.subheader("Live manufacturing setup")
    a,b = st.columns(2)
    with a:
        process = st.selectbox("Manufacturing route", ["Powder metallurgy + sintering", "Additive manufacturing", "Hot pressing", "Sol-gel coating"])
        temp = st.slider("Process temperature (°C)", 200, 1800, 950, 25)
        pressure = st.slider("Compaction / process pressure (MPa)", 1, 1000, 250, 10)
        porosity = st.slider("Final porosity (%)", 0, 60, 12)
        budget = st.number_input("Available budget (₹)", 1000, 200000, 50000, 1000)
    with b:
        process_window = {"Powder metallurgy + sintering": (800, 1300, 100, 600), "Additive manufacturing": (500, 1700, 1, 80), "Hot pressing": (700, 1500, 50, 900), "Sol-gel coating": (200, 800, 1, 30)}[process]
        temp_ok = process_window[0] <= temp <= process_window[1]
        pressure_ok = process_window[2] <= pressure <= process_window[3]
        porosity_ok = porosity <= 20
        cost_estimate = 42000 + (temp-800)*8 + pressure*4 + porosity*120
        cost_ok = cost_estimate <= budget
        st.metric("Estimated process cost (fictional ₹)", f"₹{cost_estimate:,.0f}")
        st.dataframe(pd.DataFrame({"Parameter":["Temperature window","Pressure window","Porosity target","Budget"],"Result":[temp_ok,pressure_ok,porosity_ok,cost_ok]}), hide_index=True, use_container_width=True)
        st.success("SETUP WITHIN TEACHING WINDOWS") if all([temp_ok,pressure_ok,porosity_ok,cost_ok]) else st.warning("SETUP NEEDS ADJUSTMENT")
    
    st.subheader("Candidate comparison")
    materials = {
        "Ti-6Al-4V": {"stress":180,"viability":88,"cost":450,"route":"Powder metallurgy + sintering"},
        "316L stainless": {"stress":210,"viability":83,"cost":350,"route":"Powder metallurgy + sintering"},
        "HA-Ti composite": {"stress":125,"viability":91,"cost":620,"route":"Hot pressing"},
        "PEEK": {"stress":95,"viability":89,"cost":780,"route":"Additive manufacturing"}}
    max_stress = st.number_input("Maximum design stress (MPa)", 50, 500, 220, 5)
    min_viability = st.number_input("Minimum viability (%)", 50, 100, 85, 1)
    max_cost = st.number_input("Maximum material cost (₹)", 100, 2000, 700, 25)
    rows=[]
    for name, d in materials.items():
        rows.append({"Material":name,"Stress (MPa)":d["stress"],"Viability (%)":d["viability"],"Cost (₹)":d["cost"],"Route":d["route"],"Approved":d["stress"]<=max_stress and d["viability"]>=min_viability and d["cost"]<=max_cost})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.subheader("Function and logic checks")
    mcq("m4_and", "1. Which operator requires every condition to be True?", ["A) or", "B) and", "C) not"], "B) and", "and requires all conditions to be true.")
    mcq("m4_or", "2. Which operator is True if at least one condition is True?", ["A) or", "B) and", "C) =="], "A) or", "or needs at least one True condition.")
    fill_blank("m4_dict", "3. Fill the key lookup: `sample[____]` to retrieve stress", '"stress"', "Dictionary values are retrieved using their keys.")
    fill_blank("m4_func", "4. Complete a function definition: `____ approve(sample, limits):`", "def", "def begins a function definition.")
    fill_blank("m4_tuple", "5. Fill the tuple index: `limits[____]` retrieves the minimum viability at position 1.", "1", "Tuple indexing starts at zero, so the second item is at index 1.")
    mcq("m4_compare", "6. Which expression checks that stress is at most 220 MPa AND viability is at least 85%?", ["A) stress <= 220 or viability >= 85", "B) stress <= 220 and viability >= 85", "C) stress = 220 and viability = 85"], "B) stress <= 220 and viability >= 85", "Both conditions must be true, so use and.")
    mcq("m4_function", "7. What does `return` do inside a function?", ["A) Sends a result back to the caller", "B) Repeats the function forever", "C) Prints every dictionary key"], "A) Sends a result back to the caller", "return supplies the function's result.")
    module_complete(4, ["m4_and","m4_or","m4_dict","m4_func","m4_tuple","m4_compare","m4_function"], extra_ok=all([temp_ok,pressure_ok,porosity_ok,cost_ok]))

elif page == MODULES[4]:
    header("MISSION 05", "Independent research challenge", "Use the full toolkit on a fresh steel-property dataset with fewer hints.")
    sarah()
    st.subheader("Research brief · Predict a steel batch outcome")
    st.write("A dataset contains composition and process measurements for steel batches. Your task is to calculate a simple carbon-equivalent indicator, inspect hardness and tensile strength, then classify batches using loops, lists, tuples, dictionaries, functions and logical operators.")
    st.info("For this educational task, CE* = C + Mn/6 + (Cr + Mo + V)/5. It is a simplified teaching indicator, not a substitute for a recognised weldability formula or materials standard.")
    batches = [
        {"id":"S-101","C":0.18,"Mn":1.2,"Cr":0.2,"Mo":0.05,"V":0.01,"hardness_HV":185,"UTS_MPa":520},
        {"id":"S-102","C":0.32,"Mn":1.5,"Cr":0.8,"Mo":0.2,"V":0.08,"hardness_HV":265,"UTS_MPa":780},
        {"id":"S-103","C":0.12,"Mn":0.9,"Cr":0.1,"Mo":0.02,"V":0.00,"hardness_HV":155,"UTS_MPa":430},
        {"id":"S-104","C":0.24,"Mn":1.3,"Cr":0.4,"Mo":0.1,"V":0.03,"hardness_HV":220,"UTS_MPa":640},
    ]
    st.dataframe(pd.DataFrame(batches), use_container_width=True, hide_index=True)
    st.markdown("**Your design constraints (fictional):** CE* ≤ 0.55, hardness 160–250 HV, UTS ≥ 500 MPa.")
    st.subheader("Python reasoning · assemble the analysis from code fragments")
    mcq("m5_ce", "1. Which expression matches the simplified CE* indicator shown above?", ["A) C + Mn/6 + (Cr + Mo + V)/5", "B) C × Mn × Cr", "C) C + Mn + Cr + Mo + V"], "A) C + Mn/6 + (Cr + Mo + V)/5", "Use the formula exactly as defined in this teaching exercise.")
    mcq("m5_tuple", "2. Which syntax creates a tuple containing batch ID and decision?", ["A) [batch_id, decision]", "B) (batch_id, decision)", "C) {batch_id: decision}"], "B) (batch_id, decision)", "Parentheses create a tuple.")
    mcq("m5_loop", "3. Why is a for-loop useful for the batch dataset?", ["A) It processes every batch using the same rules", "B) It changes the steel composition", "C) It guarantees every batch passes"], "A) It processes every batch using the same rules", "A loop repeats the analysis for each batch.")
    fill_blank("m5_append", "4. Complete the list operation: `results.____((batch_id, decision))`", "append", "append() adds one result tuple to the results list.")
    fill_blank("m5_func", "5. Complete the dictionary key lookup: `batch[____]` to retrieve carbon content.", '"C"', "Dictionary values are retrieved using their keys.")
    mcq("m5_logic", "6. A batch must satisfy all three limits. Which operator combines the conditions?", ["A) or", "B) and", "C) not"], "B) and", "All three requirements must be true.")
    st.subheader("Demonstration outcome")
    outcome_rows=[]
    for batch in batches:
        ce=batch["C"]+batch["Mn"]/6+(batch["Cr"]+batch["Mo"]+batch["V"])/5
        ok=ce<=0.55 and 160<=batch["hardness_HV"]<=250 and batch["UTS_MPa"]>=500
        outcome_rows.append({"Batch":batch["id"],"CE*":round(ce,3),"Decision":"ACCEPT" if ok else "REVIEW"})
    st.dataframe(pd.DataFrame(outcome_rows), use_container_width=True, hide_index=True)
    module_complete(5, ["m5_ce","m5_tuple","m5_loop","m5_append","m5_func","m5_logic"])

elif page == MODULES[5]:
    header("BONUS MISSION", "Semiconductor research lab", "A final game that combines Python with a fictional biomedical-device manufacturing workflow.")
    sarah()
    st.write("A research team is developing a thin-film sensor coating for a biomedical implant. You must guide the virtual batch through characterisation, property analysis, testing and manufacturing hurdles. Every result is fictional and educational.")
    st.subheader("Stage 1 · Characterisation")
    a,b = st.columns(2)
    with a:
        thickness = st.slider("Film thickness (nm)", 20, 500, 120)
        roughness = st.slider("Surface roughness Ra (nm)", 1, 100, 18)
        xrd_peak = st.slider("XRD peak intensity (a.u.)", 10, 1000, 620)
        defect_density = st.slider("Defect density (relative units)", 1, 100, 18)
    with b:
        char_ok = 50 <= thickness <= 250 and roughness <= 30 and xrd_peak >= 300 and defect_density <= 35
        st.metric("Characterisation gate", "PASS" if char_ok else "REWORK")
        st.write({"thickness_nm":thickness,"roughness_nm":roughness,"xrd_peak_au":xrd_peak,"defect_density":defect_density})
    st.subheader("Stage 2 · Property analysis and device testing")
    c,d = st.columns(2)
    with c:
        conductivity = st.slider("Electrical conductivity (S/m, teaching scale)", 1, 1000, 520)
        adhesion = st.slider("Film adhesion score (%)", 0, 100, 91)
        cytocompatibility = st.slider("Cell viability (%)", 0, 100, 89)
    with d:
        property_ok = conductivity >= 300 and adhesion >= 80 and cytocompatibility >= 85
        st.metric("Property gate", "PASS" if property_ok else "REVIEW")
        st.metric("Combined process status", "READY FOR FINAL HURDLE" if char_ok and property_ok else "HOLD")
    st.subheader("Stage 3 · Manufacturing hurdle")
    anneal_temp = st.slider("Annealing temperature (°C)", 100, 900, 450, 10)
    chamber_pressure = st.slider("Chamber pressure (mTorr)", 1, 100, 12)
    yield_target = st.slider("Required manufacturing yield (%)", 50, 100, 85)
    predicted_yield = max(0, min(100, 100 - abs(anneal_temp-450)*0.045 - chamber_pressure*0.25 - defect_density*0.18 - roughness*0.12))
    manufacturing_ok = 350 <= anneal_temp <= 550 and chamber_pressure <= 25 and predicted_yield >= yield_target
    st.metric("Simulated yield", f"{predicted_yield:.1f}%", "PASS" if manufacturing_ok else "BELOW TARGET")
    
    st.subheader("Stage 4 · Python mission")
    st.write("Use code blanks and MCQs to assemble the logic for a final release decision. No free-form code editor.")
    mcq("bonus_and", "1. The batch should be released only if all three gates pass. Which operator is needed?", ["A) and", "B) or", "C) not"], "A) and", "Every gate must pass.")
    fill_blank("bonus_def", "2. Complete the Boolean success value: `characterisation_pass = ____`", "True", "True is Python's Boolean success value.")
    fill_blank("bonus_return", "3. Fill both blanks in the return expression: `return characterisation ____ properties ____ manufacturing` (write the two keywords separated by a space).", "and and", "Use and between all three Boolean gate results.")
    mcq("bonus_if", "4. Which statement checks the final Boolean result?", ["A) if ready:", "B) for ready:", "C) while ready ="], "A) if ready:", "if checks whether the combined result is True.")
    fill_blank("bonus_else", "5. Complete the alternative branch: `____:`", "else", "else handles a batch that does not pass the release gate.")
    mcq("bonus_dp", "6. In dynamic programming, why store previously solved sub-problems?", ["A) To reuse results and avoid repeated work", "B) To make every answer random", "C) To remove all loops"], "A) To reuse results and avoid repeated work", "Dynamic programming stores solved sub-problems for reuse.")

    st.subheader("Stage 5 · Advanced bonus: recursion / dynamic programming")
    st.write("A tiny planning puzzle: find the minimum number of inspection steps needed to reach a target reliability score. This is a toy dynamic-programming exercise, not a real qualification method.")
    target = st.slider("Target score", 5, 30, 12)
    steps = (1, 3, 5)
    dp=[0]+[999]*target
    for i in range(1,target+1):
        for step in steps:
            if i>=step: dp[i]=min(dp[i],dp[i-step]+1)
    st.metric("Minimum toy planning steps", dp[target])
    bonus_keys = ["bonus_and","bonus_def","bonus_return","bonus_if","bonus_else","bonus_dp"]
    bonus_quiz_done = all(k in st.session_state.correct for k in bonus_keys)
    if bonus_quiz_done and char_ok and property_ok and manufacturing_ok:
        st.session_state.done.add(6)
        st.session_state.Sarah=6
        st.balloons()
        st.success("BONUS COMPLETE! Sarah is now a Python Semiconductor Engineer specialised in biomedical-device research. 🥳")
        sarah(6)
    else:
        st.info("Complete all six Python checks and pass all three laboratory gates to complete the bonus mission.")

elif page == "🛠 Admin Panel":
    if not st.session_state.admin_authenticated:
        st.error("Admin authentication required.")
        st.stop()

    header("ADMIN CONSOLE", "ImplantLab control room", "Manage the local learning session, scoring rules and learner progress.")
    sarah(message="Admin access recognised! The lab administrator can now manage this training session. 🔐")

    st.subheader("1 · Scoring rules")
    c1, c2 = st.columns(2)
    with c1:
        new_xp = st.number_input("Points for a correct answer", min_value=0, max_value=100,
                                 value=int(st.session_state.xp_correct), step=1, key="admin_xp_correct")
    with c2:
        new_penalty = st.number_input("Points deducted for a wrong answer", min_value=0, max_value=100,
                                      value=int(st.session_state.xp_penalty), step=1, key="admin_xp_penalty")
    if st.button("Save scoring rules", key="admin_save_scoring"):
        st.session_state.xp_correct = int(new_xp)
        st.session_state.xp_penalty = int(new_penalty)
        st.success("Scoring rules updated for this session.")

    st.divider()
    st.subheader("2 · Learner progress and open module access")
    c1, c2, c3 = st.columns(3)
    c1.metric("Current XP", st.session_state.score)
    c2.metric("Modules completed", f"{len(st.session_state.done)}/6")
    c3.metric("Correct answers", len(st.session_state.correct))
    st.success("All six learning modules and the Research Sandbox are available to learners from the start.")

    c1, c2 = st.columns(2)
    with c1:
        score_adjustment = st.number_input("Adjust learner XP (+/-)", min_value=-1000, max_value=1000,
                                            value=0, step=5, key="admin_score_adjust")
        if st.button("Apply XP adjustment", key="admin_adjust_score"):
            st.session_state.score = max(0, int(st.session_state.score + score_adjustment))
            if st.session_state.score == 0:
                reset_campaign()
                st.warning("Score reached zero; campaign reset to Module 1.")
            else:
                st.success("Learner XP updated.")
            st.rerun()
    with c2:
        st.write("**Reset learner campaign**")
        st.caption("Clears score, completed modules and exercise answers.")
        confirm_reset = st.checkbox("I confirm the campaign reset", key="admin_confirm_reset")
        if st.button("Reset campaign", key="admin_reset_campaign", disabled=not confirm_reset):
            reset_campaign()
            st.success("Campaign reset to Module 1.")
            st.rerun()

    st.divider()
    st.subheader("3 · Learner activity")
    st.write({
        "completed_modules": sorted(st.session_state.done),
        "module_access": "all modules open",
        "correct_exercises": sorted(st.session_state.correct),
        "wrong_exercises": sorted(st.session_state.wrong),
        "attempted_exercises": sorted(st.session_state.attempted),
        "sarah_level": st.session_state.Sarah
    })
    st.info("Admin changes apply to the current Streamlit session. This starter build does not yet include student accounts, a shared database, or persistent multi-user analytics.")

elif page == "Research Sandbox":
    header("OPEN LAB", "Research sandbox", "Keep experimenting with the original interactive stress-screening bench.")
    a,b=st.columns(2)
    with a:
        force=st.number_input("Applied force (N)",100.0,10000.0,2500.0,100.0)
        area=st.number_input("Cross-sectional area (mm²)",1.0,100.0,12.5,0.5)
        viability=st.slider("Average cell viability (%)",0.0,100.0,87.75,0.25)
        cost=st.number_input("Unit cost (₹)",0,100000,4500,250)
        sl=st.number_input("Stress limit (MPa)",1.0,1000.0,220.0,5.0)
        vl=st.number_input("Viability threshold (%)",0.0,100.0,85.0,1.0)
        bl=st.number_input("Budget (₹)",0,100000,7000,250)
    stress=force/area
    checks=[stress<=sl,viability>=vl,cost<=bl]
    with b:
        st.metric("Calculated stress",f"{stress:.2f} MPa")
        st.metric("Overall screen","PASS" if all(checks) else "NOT PASSED")
        st.dataframe(pd.DataFrame({"Criterion":["Stress","Cell viability","Budget"],"Status":["Pass" if x else "Fail" for x in checks]}),hide_index=True,use_container_width=True)
        chart=pd.DataFrame({"Force (N)":list(range(500,5001,250))})
        chart["Stress (MPa)"]=chart["Force (N)"]/area
        fig=px.line(chart,x="Force (N)",y="Stress (MPa)",title=f"Stress vs force at area {area:g} mm²")
        fig.add_hline(y=sl,line_dash="dash",annotation_text="Stress limit")
        fig.add_vline(x=force,line_dash="dot",annotation_text="Current force")
        fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
st.divider()
st.caption("Disclaimer: All datasets, experimental outcomes, reference values and process windows shown in ImplantLab are fictional, created for Python-learning demonstrations. They are not actual experimental results, validated specifications, clinical evidence or manufacturing instructions.")
