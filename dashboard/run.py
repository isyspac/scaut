import streamlit as st
from scaut.scan.utils import plot_generic_data, plot_response_matrix, get_meters_data, set_motors_values
import settings
from app_utils import scan_for_data_files, format_file_name, prepare_step_range, load_json_file, load_uploaded_data, get_available_plots
import pandas as pd
import numpy as np

def update_motor_value(editor_key, step_key):
    edited_data = st.session_state[editor_key]
    for index, row in edited_data["edited_rows"].items():
        motor = row.get("Motor")
        if motor:
            st.session_state.edited_motor_values[step_key][motor] = row.get("Set value", 0.0)
    st.session_state.value_changed = True

def display_motor_controls(scan_data, last_step):
    if not scan_data or "steps" not in scan_data or not scan_data["steps"]:
        st.sidebar.warning("No step data available for motor control")
        return
    
    st.sidebar.subheader("Motor Control")
    
    steps = scan_data.get("steps", [])
    selected_step = next((step for step in steps if step.get("step_index") == last_step), None)
    
    if not selected_step:
        st.sidebar.warning(f"Step {last_step} not found in data")
        return
    
    if "motor_values" in selected_step:
        motor_values = selected_step["motor_values"]
        motor_names = list(motor_values.keys())
        
        if "edited_motor_values" not in st.session_state:
            st.session_state.edited_motor_values = {}
        
        step_key = f"step_{last_step}"
        if step_key not in st.session_state.edited_motor_values:
            st.session_state.edited_motor_values[step_key] = {motor: motor_values[motor] for motor in motor_names}
        
        for motor in motor_names:
            if motor not in st.session_state.edited_motor_values[step_key]:
                st.session_state.edited_motor_values[step_key][motor] = motor_values[motor]
        
        all_motors_option = "Select All"
        motor_options = [all_motors_option] + motor_names
        
        selected_motors = st.sidebar.multiselect(
            "Select motors to set values",
            options=motor_options,
            default=[],
            key=f"multiselect_motors_{last_step}"
        )
        
        if all_motors_option in selected_motors:
            selected_motors = motor_names
        
        with st.spinner("Getting current motor values..."):
            try:
                current_values, _ = get_meters_data(motor_names, settings.GET_FUNC, sample_size=settings.SAMPLE_SIZE)
            except Exception as e:
                st.sidebar.error(f"Error getting current motor values: {e}")
                current_values = {motor: 0.0 for motor in motor_names}
                
        data = []
        for motor in selected_motors:
            data.append({
                "Motor": motor,
                "Set value": st.session_state.edited_motor_values[step_key][motor],
                "Current value": current_values.get(motor, "N/A"),
                "Difference": np.round(st.session_state.edited_motor_values[step_key][motor] - current_values.get(motor, 0.0), 6) 
                    if motor in current_values else "N/A"
            })
            
        df = pd.DataFrame(data)
        
        if "value_changed" not in st.session_state:
            st.session_state.value_changed = False
            
        editor_key = f"motor_table_{last_step}"
        
        if not df.empty:
            edited_df = st.sidebar.data_editor(
                df,
                column_config={
                    "Motor": st.column_config.TextColumn("Motor", disabled=True),
                    "Set value": st.column_config.NumberColumn("Set value", format="%.6f"),
                    "Current value": st.column_config.NumberColumn("Current value", format="%.6f", disabled=True),
                    "Difference": st.column_config.NumberColumn("Difference", format="%.6f", disabled=True),
                },
                hide_index=True,
                key=editor_key,
                on_change=update_motor_value,
                args=(editor_key, step_key)
            )
        
        if st.session_state.value_changed:
            st.session_state.value_changed = False
            st.rerun()
            
        if st.sidebar.button("Set Selected Motor Values"):
            if not selected_motors:
                st.sidebar.warning("No motors selected")
            else:
                values = [st.session_state.edited_motor_values[step_key][m] for m in selected_motors]
                status = put_values_to_motors(selected_motors, values)
    else:
        st.sidebar.warning("No motor values found in the selected step")

def put_values_to_motors(motor_names, values):
    if not motor_names or not values:
        st.sidebar.warning("No motors or values to set")
        return False
    
    try:
        set_motors_values(
            motor_names=motor_names,
            combination=values,
            get_func=settings.GET_FUNC,
            put_func=settings.PUT_FUNC,
            verify_motor=settings.VERIFY_MOTOR,
            max_retries=settings.MAX_RETRIES,
            delay=settings.DELAY,
            tolerance=settings.TOLERANCE,
            parallel=settings.PARALLEL,
        )
        st.sidebar.success(f"Set values for {len(motor_names)} motors")
        return True
            
    except Exception as e:
        st.sidebar.error(f"Error setting motor values: {e}")
        return False
            

def main():
    st.set_page_config(
        page_title="SCAUT Dashboard",
        page_icon="snowflake",
        layout="wide",
    )
    st.title("SCAUT Data Visualization Dashboard")

    default_files = scan_for_data_files()

    st.sidebar.header("Data Source")
    source_type = st.sidebar.radio("Select data source:", ["Default Dataset", "Upload Custom File"])

    scan_data = None

    if source_type == "Default Dataset":
        if not default_files:
            st.error("No default files found. Please upload a custom file.")
            return

        file_options = {format_file_name(name, size): path for name, [path, size] in default_files.items()}

        selected_display = st.sidebar.selectbox("Select default dataset", list(file_options.keys()))
        file_path = file_options[selected_display]

        try:
            scan_data = load_json_file(file_path)
            st.sidebar.success(f"Loaded: {selected_display}")
            st.sidebar.caption(f"File: {file_path.name}")
        except Exception as e:
            st.error(f"Error loading default file: {e}")
            return

    else:
        uploaded_file = st.sidebar.file_uploader("Choose a JSON file", type="json")

        if uploaded_file is None:
            if default_files:
                first_file, size = next(iter(default_files.values()))
                display_name = format_file_name(first_file.name, size)
                st.info(f"Using default dataset: {display_name}")
                try:
                    scan_data = load_json_file(first_file)
                except Exception as e:
                    st.error(f"Error loading default file: {e}")
                    return
            else:
                st.warning("Please upload a JSON file or add default files")
                return
        else:
            try:
                scan_data = load_uploaded_data(uploaded_file)
                st.sidebar.success("File uploaded successfully!")
                st.sidebar.caption(f"File: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error loading file: {e}")
                return

    has_response_matrix = "response_measurements" in scan_data

    all_steps = scan_data.get("steps", [])
    has_steps = bool(all_steps)

    if not has_steps and not has_response_matrix:
        st.error("No steps found in the data and no response matrix available")
        return

    last_step = 0
    if has_steps:
        max_step_index = len(all_steps) - 1

        st.sidebar.header("Step Controls")
        num_steps = st.sidebar.slider("Number of Steps to Show", 1, 10, settings.DEFAULT_NUM_STEPS)
        last_step = st.sidebar.slider("Last Step Index", 0, max_step_index, max_step_index)
        step_range = prepare_step_range(last_step, num_steps, max_step_index)
        displayed_steps = scan_data["steps"][step_range[0]:step_range[1]:step_range[2]]
        
        full_steps = scan_data["steps"].copy()
        scan_data["steps"] = displayed_steps

    st.sidebar.header("Plot Configuration")
    available_plots = get_available_plots(scan_data) if has_steps else []

    tab_names = [cfg["name"] for cfg in available_plots]
    if has_response_matrix:
        tab_names.append("Response Matrix")

    if not available_plots and not has_response_matrix and not has_steps:
        st.error("No valid data found in the file")
        return

    st.sidebar.header("Figure Settings")
    fig_width = st.sidebar.slider("Figure Width", 5, 40, settings.DEFAULT_FIG_WIDTH)
    fig_height = st.sidebar.slider("Figure Height per Plot", 3, 10, settings.DEFAULT_FIG_HEIGHT_PER_PLOT)

    tabs = st.tabs(tab_names)

    for i, cfg in enumerate(available_plots):
        with tabs[i]:
            fig = plot_generic_data(
                scan_data=scan_data,
                items_key=cfg["items_key"],
                step_value_key=cfg["value_key"],
                title=f"{cfg['name']} Data",
                xlabel="Devices",
                ylabel="Values",
                step_range=step_range,
                limits_key=cfg["limits_key"],
                errors_key=cfg["errors_key"],
                fig_size_x=fig_width,
                fig_size_y=fig_height
            )

            if fig:
                st.pyplot(fig)
                last_step_display = last_step + 1
                st.caption(f"Figure {i + 1}: {cfg['name']} data visualization showing {num_steps} steps. "
                           f"Black markers indicate the most recent step ({last_step_display}).")
            else:
                st.error(f"No {cfg['name']} data to display with current settings")

    if has_response_matrix:
        response_tab_index = len(available_plots)
        with tabs[response_tab_index]:
            st.subheader("Response Matrix")
            try:
                fig = plot_response_matrix(scan_data)
                if fig:
                    st.pyplot(fig)
                    st.caption("Response matrix visualization showing the relationship between inputs and outputs.")
                else:
                    st.warning("Response matrix data is present but could not be visualized.")
            except Exception as e:
                st.error(f"Error plotting response matrix: {e}")
                st.exception(e)
    
    if st.sidebar.checkbox("Show Raw Data"):
        st.subheader("Raw Data")
        if has_steps:
            st.json(scan_data["steps"])
        if has_response_matrix:
            st.subheader("Response Matrix Data")
            st.json(scan_data["response_measurements"])

    if has_steps:
        motors_tab_index = len(tab_names) - 1
        with tabs[motors_tab_index]:
            scan_data_for_motors = scan_data.copy()
            scan_data_for_motors["steps"] = full_steps
            
            display_motor_controls(scan_data_for_motors, last_step)


if __name__ == "__main__":
    main()